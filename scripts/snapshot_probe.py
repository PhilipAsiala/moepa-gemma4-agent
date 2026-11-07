#!/usr/bin/env python3
"""Offline snapshot probe: extract tarball, apply gold / agent edits, syntax + axiology.

This does **not** claim official pytest resolve rate unless deps install cleanly.
It measures whether:
  1) gold patches apply to the shipped snapshot
  2) modified files still parse
  3) Axiology accepts the resulting diff
  4) (optional) Gemma proposes an edit that applies and parses

Usage:
  .venv/bin/python scripts/snapshot_probe.py --limit 12
  .venv/bin/python scripts/snapshot_probe.py --limit 12 --with-gemma --model gemma4:12b
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from moepa.agent import MOEPAGemmaAgent  # noqa: E402
from moepa.axiology import AxiologyPolicyGate  # noqa: E402
from moepa.epistemology import EpistemologyVerifier  # noqa: E402
from moepa.llm_ollama import OllamaClient  # noqa: E402
from moepa.ontology import OntologySubstrate  # noqa: E402

DATA = ROOT / "data"
OUT = ROOT / "outputs" / "snapshot_probe.json"


def load_tasks():
    rows = []
    for line in (DATA / "tasks.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def stem_for(task: dict) -> str:
    return f"{task['repo'].split('/')[-1]}_{task['base_commit']}"


def snapshot_tgz(task: dict) -> Path:
    return DATA / "snapshots" / f"{task['instance_id']}.tgz"


def extract_snapshot(tgz: Path, dest: Path) -> Path:
    """Extract a competition snapshot tarball.

    Archives are rooted at ``.`` (contain ``./.git``, ``./fastapi``, …), so the
    extract directory *is* the repo. Only unwrap a single nested folder when the
    archive uses that layout.
    """
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(["tar", "-xzf", str(tgz), "-C", str(dest)], check=True)
    children = [p for p in dest.iterdir() if p.name not in {".", ".."}]
    interesting = [p for p in children if p.name != ".git"]
    if len(interesting) == 1 and interesting[0].is_dir() and not (dest / ".git").exists():
        return interesting[0]
    return dest


def ensure_git(repo: Path) -> None:
    """Snapshots already ship a .git directory; only init if missing."""
    if (repo / ".git").exists():
        # Ensure a clean index relative to HEAD for apply/diff.
        subprocess.run(
            ["git", "reset", "--hard", "HEAD"],
            cwd=str(repo),
            check=False,
            capture_output=True,
        )
        subprocess.run(
            ["git", "clean", "-fd"],
            cwd=str(repo),
            check=False,
            capture_output=True,
        )
        return
    subprocess.run(["git", "init"], cwd=str(repo), check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=str(repo), check=True, capture_output=True)
    env = {
        **__import__("os").environ,
        "GIT_AUTHOR_NAME": "moepa",
        "GIT_AUTHOR_EMAIL": "moepa@local",
        "GIT_COMMITTER_NAME": "moepa",
        "GIT_COMMITTER_EMAIL": "moepa@local",
    }
    subprocess.run(
        ["git", "commit", "-m", "base", "--allow-empty"],
        cwd=str(repo),
        check=True,
        capture_output=True,
        env=env,
    )


def apply_patch(repo: Path, patch: str) -> tuple[bool, str]:
    if not patch.strip():
        return False, "empty"
    # JSONL often drops the final newline; git apply then reports "corrupt patch".
    if not patch.endswith("\n"):
        patch = patch + "\n"
    proc = subprocess.run(
        ["git", "apply", "--whitespace=nowarn", "-"],
        cwd=str(repo),
        input=patch,
        text=True,
        capture_output=True,
    )
    if proc.returncode == 0:
        return True, "applied"
    return False, (proc.stderr or proc.stdout or "apply_failed")[:500]


def changed_py_files(repo: Path) -> list[Path]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    files = []
    for line in proc.stdout.splitlines():
        path = repo / line.strip()
        if path.suffix == ".py" and path.exists():
            files.append(path)
    return files


def probe_task(task: dict, *, with_gemma: bool, model: str) -> dict:
    tgz = snapshot_tgz(task)
    row = {
        "instance_id": task["instance_id"],
        "repo": task["repo"],
        "snapshot_exists": tgz.exists(),
        "gold_apply": False,
        "gold_syntax_ok": False,
        "gold_axiology_ok": False,
        "gemma_ran": False,
        "gemma_diff": None,
        "gemma_syntax_ok": False,
        "gemma_axiology_ok": False,
        "seconds": None,
        "error": None,
    }
    if not tgz.exists():
        row["error"] = f"missing {tgz.name}"
        return row

    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="moepa_snap_") as tmp:
        root = Path(tmp)
        try:
            repo = extract_snapshot(tgz, root / "src")
            ensure_git(repo)
            ok, msg = apply_patch(repo, task["patch"])
            row["gold_apply"] = ok
            if not ok:
                row["error"] = f"gold_apply:{msg}"
                return row
            py_files = changed_py_files(repo)
            syntax = [
                EpistemologyVerifier.verify_python_syntax(path)[0] for path in py_files
            ]
            row["gold_syntax_ok"] = all(syntax) if syntax else True
            diff = subprocess.run(
                ["git", "diff", "HEAD"],
                cwd=str(repo),
                capture_output=True,
                text=True,
            ).stdout
            ax_ok, _ = AxiologyPolicyGate.evaluate_patch_policy(diff)
            row["gold_axiology_ok"] = ax_ok

            if with_gemma:
                # Reset to pristine snapshot for agent attempt.
                shutil.rmtree(repo)
                repo = extract_snapshot(tgz, root / "agent")
                ensure_git(repo)
                gpath = DATA / "graphs" / f"{stem_for(task)}.json"
                epath = DATA / "embeddings" / f"{stem_for(task)}.npz"
                ont = OntologySubstrate(gpath, epath if epath.exists() else None)
                llm = OllamaClient(model=model, num_predict=4096)
                # Skip pytest here: public snapshots need competition wheels/sandbox.
                # We still gate on syntax + Axiology (static Epistemology + policy).
                agent = MOEPAGemmaAgent(llm, repo, ont, run_pytest=False)
                agent_result = agent.solve_task(task)
                row["gemma_ran"] = True
                row["gemma_diff"] = (
                    agent_result[:2000]
                    if isinstance(agent_result, str)
                    else str(agent_result)
                )
                if agent_result and agent_result != "NO_PATCH":
                    # Agent already left edits applied when returning a diff.
                    # Re-check from returned text via axiology; syntax already gated.
                    ax2, _ = AxiologyPolicyGate.evaluate_patch_policy(agent_result)
                    row["gemma_axiology_ok"] = ax2
                    row["gemma_syntax_ok"] = True
        except Exception as exc:  # noqa: BLE001
            row["error"] = str(exc)[:500]
        finally:
            row["seconds"] = round(time.monotonic() - started, 2)
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--with-gemma", action="store_true")
    parser.add_argument("--model", default="gemma4:12b")
    parser.add_argument("--seed", type=int, default=20261107)
    args = parser.parse_args()

    tasks = load_tasks()
    # Prefer tasks that have snapshots and single-file gold patches.
    eligible = [
        t
        for t in tasks
        if snapshot_tgz(t).exists()
        and sum(1 for ln in t["patch"].splitlines() if ln.startswith("+++ b/")) == 1
    ]
    eligible.sort(key=lambda t: t["instance_id"])
    chosen = eligible[: args.limit]
    if not chosen:
        # Fall back to any tasks with snapshots.
        chosen = [t for t in tasks if snapshot_tgz(t).exists()][: args.limit]

    print(f"probing {len(chosen)} tasks; snapshots dir={DATA / 'snapshots'}", flush=True)
    rows = []
    for task in chosen:
        row = probe_task(task, with_gemma=args.with_gemma, model=args.model)
        rows.append(row)
        print(
            f"{row['instance_id']} gold_apply={row['gold_apply']} "
            f"syntax={row['gold_syntax_ok']} ax={row['gold_axiology_ok']} "
            f"gemma={row['gemma_diff'] is not None and row['gemma_diff'] != 'NO_PATCH'} "
            f"err={row['error']}",
            flush=True,
        )

    summary = {
        "n": len(rows),
        "gold_apply": sum(r["gold_apply"] for r in rows),
        "gold_syntax_ok": sum(r["gold_syntax_ok"] for r in rows),
        "gold_axiology_ok": sum(r["gold_axiology_ok"] for r in rows),
        "gemma_patch": sum(
            1
            for r in rows
            if r.get("gemma_diff") and r["gemma_diff"] != "NO_PATCH"
        ),
        "gemma_axiology_ok": sum(r["gemma_axiology_ok"] for r in rows),
        "with_gemma": args.with_gemma,
        "model": args.model if args.with_gemma else None,
        "rows": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
