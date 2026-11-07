#!/usr/bin/env python3
"""Fail-to-pass pytest resolve probe using competition wheels + Python 3.13 Docker.

Host Python here is 3.14, but competition wheels ship cp312/cp313 binaries
(pydantic-core, markupsafe, …). Verification therefore runs inside
``python:3.13-slim`` with ``data/wheels`` mounted read-only.

For each task with a local snapshot:
  1. extract snapshot
  2. apply gold patch + test_patch (or agent edit + test_patch)
  3. ``docker run python:3.13-slim`` → offline pip from /wheels → pytest

This is a local Epistemology Phase-C proxy, not the official swegemma
two-container harness.

Usage:
  .venv/bin/python scripts/pytest_resolve_probe.py --limit 20
  .venv/bin/python scripts/pytest_resolve_probe.py --limit 8 --with-gemma --model gemma4:12b
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Sequence

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from moepa.agent import MOEPAGemmaAgent  # noqa: E402
from moepa.axiology import AxiologyPolicyGate  # noqa: E402
from moepa.llm_ollama import OllamaClient  # noqa: E402
from moepa.ontology import OntologySubstrate  # noqa: E402

DATA = ROOT / "data"
WHEELS = DATA / "wheels"
OUT = ROOT / "outputs" / "pytest_resolve.json"
DOCKER_IMAGE = os.environ.get("MOEPA_PYTEST_IMAGE", "python:3.13-slim")

# Third-party deps only. Snapshot source stays on PYTHONPATH so edits are visible.
REPO_PACKAGES = {
    "Textualize/rich": ["markdown-it-py", "mdurl", "pygments"],
    "fastapi/fastapi": [
        # Match fastapi pyproject: starlette>=0.40,<0.49 (1.x wants httpx2).
        "starlette==0.48.0",
        "pydantic==2.13.4",
        "pydantic-core",
        "typing-inspection",
        "typing-extensions",
        "annotated-types",
        "annotated-doc",
        "anyio",
        "idna",
        "sniffio",
        "certifi",
        "jinja2",
        "markupsafe",
        "httpx",
        "httpcore",
        "h11",
        "python-multipart",
    ],
    "psf/requests": [
        "urllib3",
        "certifi",
        "charset-normalizer",
        "idna",
        "flask",
        "werkzeug",
        "pytest-httpbin",
        "httpbin",
        "decorator",
        "blinker",
        "itsdangerous",
        "click",
        "jinja2",
        "markupsafe",
        "brotlicffi",
        "greenlet",
    ],
    "encode/httpx": [
        "httpcore",
        "anyio",
        "idna",
        "certifi",
        "sniffio",
        "h11",
    ],
}


def load_tasks() -> List[dict]:
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
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(["tar", "-xzf", str(tgz), "-C", str(dest)], check=True)
    children = [p for p in dest.iterdir() if p.name not in {".", ".."}]
    interesting = [p for p in children if p.name != ".git"]
    if len(interesting) == 1 and interesting[0].is_dir() and not (dest / ".git").exists():
        return interesting[0]
    return dest


def ensure_clean(repo: Path) -> None:
    if (repo / ".git").exists():
        subprocess.run(
            ["git", "reset", "--hard", "HEAD"], cwd=str(repo), capture_output=True
        )
        subprocess.run(["git", "clean", "-fd"], cwd=str(repo), capture_output=True)


def apply_patch(repo: Path, patch: str) -> tuple[bool, str]:
    if not patch.strip():
        return False, "empty"
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
    return False, (proc.stderr or proc.stdout or "apply_failed")[:400]


def test_files_from_patch(test_patch: str) -> List[str]:
    files = []
    for ln in test_patch.splitlines():
        if ln.startswith("+++ b/"):
            path = ln[6:].strip()
            if path not in files:
                files.append(path)
    return files


def added_test_names(test_patch: str) -> List[str]:
    import re

    # Only newly added defs (diff lines beginning with '+', not '+++').
    return list(
        dict.fromkeys(
            re.findall(r"^\+ *def (test_\w+)\s*\(", test_patch, flags=re.M)
        )
    )


def pytest_targets_from_patch(test_patch: str) -> List[str]:
    """Return pytest args: file path plus optional -k expression.

    Added tests may be class methods (need -k) or module-level (file::name).
    Running a whole pre-existing suite pulls fixtures the wheel shelf lacks.
    """
    files = test_files_from_patch(test_patch)
    names = added_test_names(test_patch)
    if not files:
        return []
    if not names:
        return files
    # file + -k keeps class-based tests selectable without knowing the class.
    expr = " or ".join(names)
    return [*files, "-k", expr]


def pythonpath_mount(repo: Path) -> str:
    parts = ["/workspace"]
    if (repo / "src").is_dir():
        parts.append("/workspace/src")
    return ":".join(parts)


def docker_available() -> bool:
    try:
        proc = subprocess.run(
            ["docker", "image", "inspect", DOCKER_IMAGE],
            capture_output=True,
            text=True,
        )
        return proc.returncode == 0
    except FileNotFoundError:
        return False


def run_pytest_docker(
    repo: Path,
    task: dict,
    tests: Sequence[str],
    venv_dir: Path,
    timeout: float = 180.0,
) -> tuple[bool, str]:
    pkgs = ["pytest", *REPO_PACKAGES.get(task["repo"], [])]
    # Venv lives outside the git worktree so `git clean` does not wipe it.
    install_bits = [
        f'/venv/bin/pip install -q --no-index --find-links=/wheels "{pkg}" || true'
        for pkg in pkgs
    ]
    install = " && ".join(install_bits)
    pp = pythonpath_mount(repo)
    test_args = " ".join(f'"{t}"' for t in tests)
    script = (
        "set -e; "
        "if [ ! -x /venv/bin/python ]; then python -m venv /venv; fi; "
        f"{install}; "
        f"export PYTHONPATH={pp}; "
        f"/venv/bin/python -m pytest -q --tb=line --disable-warnings {test_args}"
    )
    uid = os.getuid()
    gid = os.getgid()
    venv_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "docker",
        "run",
        "--rm",
        "--user",
        f"{uid}:{gid}",
        "-e",
        "HOME=/tmp",
        "-e",
        "PYTHONDONTWRITEBYTECODE=1",
        "-v",
        f"{WHEELS.resolve()}:/wheels:ro",
        "-v",
        f"{repo.resolve()}:/workspace",
        "-v",
        f"{venv_dir.resolve()}:/venv",
        "-w",
        "/workspace",
        DOCKER_IMAGE,
        "bash",
        "-lc",
        script,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT_FAULT"
    tail = (proc.stdout + "\n" + proc.stderr).strip().splitlines()
    summary = "\n".join(tail[-16:]) if tail else "no_output"
    return proc.returncode == 0, summary


def probe_gold(task: dict) -> dict:
    tgz = snapshot_tgz(task)
    row = {
        "instance_id": task["instance_id"],
        "repo": task["repo"],
        "gold_resolve": False,
        "fail_baseline": None,
        "setup": f"docker:{DOCKER_IMAGE}",
        "error": None,
        "seconds": None,
        "tests": pytest_targets_from_patch(task.get("test_patch") or ""),
    }
    if not tgz.exists():
        row["error"] = "missing_snapshot"
        return row
    if not WHEELS.exists() or not any(WHEELS.glob("*.whl")):
        row["error"] = "missing_wheels"
        return row
    if not docker_available():
        row["error"] = f"missing_docker_image:{DOCKER_IMAGE}"
        return row
    started = time.monotonic()
    with tempfile.TemporaryDirectory(
        prefix="moepa_resolve_", ignore_cleanup_errors=True
    ) as tmp:
        root = Path(tmp)
        try:
            repo = extract_snapshot(tgz, root / "src")
            ensure_clean(repo)
            tests = row["tests"]
            if not tests:
                row["error"] = "no_test_files"
                return row

            venv_dir = root / "venv"
            ok_t, msg_t = apply_patch(repo, task["test_patch"])
            if not ok_t:
                row["error"] = f"test_patch:{msg_t}"
                return row
            fail_ok, fail_msg = run_pytest_docker(repo, task, tests, venv_dir)
            row["fail_baseline"] = not fail_ok
            if fail_ok:
                row["error"] = f"baseline_already_passing:{fail_msg[:200]}"

            ensure_clean(repo)
            ok_g, msg_g = apply_patch(repo, task["patch"])
            if not ok_g:
                row["error"] = f"gold_apply:{msg_g}"
                return row
            ok_t2, msg_t2 = apply_patch(repo, task["test_patch"])
            if not ok_t2:
                row["error"] = f"test_patch_after_gold:{msg_t2}"
                return row
            pass_ok, pass_msg = run_pytest_docker(repo, task, tests, venv_dir)
            row["gold_resolve"] = pass_ok
            if not pass_ok and not (row["error"] or "").startswith("baseline_"):
                row["error"] = pass_msg[:500]
            elif pass_ok:
                row["error"] = None if row["fail_baseline"] else row["error"]
        except Exception as exc:  # noqa: BLE001
            row["error"] = str(exc)[:500]
        finally:
            row["seconds"] = round(time.monotonic() - started, 2)
    return row


def probe_agent(task: dict, model: str) -> dict:
    """Run MOEPA agent with Docker wheel-backed pytest gate on one task."""
    tgz = snapshot_tgz(task)
    row = {
        "instance_id": task["instance_id"],
        "repo": task["repo"],
        "agent_patch": False,
        "agent_axiology_ok": False,
        "agent_resolve": False,
        "error": None,
        "seconds": None,
        "diff_preview": None,
        "setup": f"docker:{DOCKER_IMAGE}",
    }
    if not tgz.exists():
        row["error"] = "missing_snapshot"
        return row
    started = time.monotonic()
    with tempfile.TemporaryDirectory(
        prefix="moepa_agent_", ignore_cleanup_errors=True
    ) as tmp:
        root = Path(tmp)
        try:
            repo = extract_snapshot(tgz, root / "src")
            ensure_clean(repo)
            tests = pytest_targets_from_patch(task.get("test_patch") or "")
            ok_t, msg_t = apply_patch(repo, task["test_patch"])
            if not ok_t:
                row["error"] = f"test_patch:{msg_t}"
                return row
            subprocess.run(["git", "add", "-A"], cwd=str(repo), capture_output=True)
            env = {
                **os.environ,
                "GIT_AUTHOR_NAME": "moepa",
                "GIT_AUTHOR_EMAIL": "moepa@local",
                "GIT_COMMITTER_NAME": "moepa",
                "GIT_COMMITTER_EMAIL": "moepa@local",
            }
            subprocess.run(
                ["git", "commit", "-m", "test_patch", "--allow-empty"],
                cwd=str(repo),
                capture_output=True,
                env=env,
            )

            gpath = DATA / "graphs" / f"{stem_for(task)}.json"
            epath = DATA / "embeddings" / f"{stem_for(task)}.npz"
            ont = OntologySubstrate(gpath, epath if epath.exists() else None)
            llm = OllamaClient(model=model, num_predict=4096)

            from moepa import epistemology as epi

            venv_dir = root / "venv"

            def _verify(repo_dir: Path, timeout_sec: float, **_kwargs):
                return run_pytest_docker(
                    Path(repo_dir),
                    task,
                    tests,
                    venv_dir,
                    timeout=max(60.0, timeout_sec),
                )

            epi.EpistemologyVerifier.run_verification_tests = staticmethod(_verify)

            agent = MOEPAGemmaAgent(llm, repo, ont, run_pytest=True)
            result = agent.solve_task(task)
            if result and result != "NO_PATCH":
                row["agent_patch"] = True
                row["diff_preview"] = result[:1500]
                ax_ok, _ = AxiologyPolicyGate.evaluate_patch_policy(result)
                row["agent_axiology_ok"] = ax_ok
                ok, msg = run_pytest_docker(repo, task, tests, venv_dir)
                row["agent_resolve"] = ok
                if not ok:
                    row["error"] = msg[:400]
            else:
                row["error"] = "NO_PATCH"
        except Exception as exc:  # noqa: BLE001
            row["error"] = str(exc)[:500]
        finally:
            row["seconds"] = round(time.monotonic() - started, 2)
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--with-gemma", action="store_true")
    parser.add_argument("--gemma-limit", type=int, default=3)
    parser.add_argument("--model", default="gemma4:12b")
    args = parser.parse_args()

    if not WHEELS.exists() or not any(WHEELS.glob("*.whl")):
        raise SystemExit(f"Need competition wheels under {WHEELS}.")
    if not docker_available():
        raise SystemExit(
            f"Need Docker image {DOCKER_IMAGE}. Run: docker pull {DOCKER_IMAGE}"
        )

    tasks = load_tasks()
    eligible = [
        t
        for t in tasks
        if snapshot_tgz(t).exists()
        and (t.get("test_patch") or "").strip()
        and sum(1 for ln in t["patch"].splitlines() if ln.startswith("+++ b/")) == 1
    ]
    # Stratify across repos so FastAPI does not monopolize --limit.
    by_repo: dict[str, list] = {}
    for t in eligible:
        by_repo.setdefault(t["repo"], []).append(t)
    for repo in by_repo:
        by_repo[repo].sort(key=lambda t: t["instance_id"])
    chosen = []
    repos = sorted(by_repo)
    while len(chosen) < args.limit and any(by_repo.values()):
        for repo in repos:
            if by_repo[repo] and len(chosen) < args.limit:
                chosen.append(by_repo[repo].pop(0))
    print(
        f"gold resolve probe n={len(chosen)} wheels={WHEELS} image={DOCKER_IMAGE}",
        flush=True,
    )

    gold_rows = []
    for task in chosen:
        row = probe_gold(task)
        gold_rows.append(row)
        print(
            f"{row['instance_id']} resolve={row['gold_resolve']} "
            f"fail_base={row['fail_baseline']} err={row['error']}",
            flush=True,
        )

    agent_rows = []
    if args.with_gemma:
        good = [r["instance_id"] for r in gold_rows if r["gold_resolve"]]
        by_id = {t["instance_id"]: t for t in chosen}
        agent_tasks = [by_id[i] for i in good[: args.gemma_limit] if i in by_id]
        if len(agent_tasks) < args.gemma_limit:
            for t in chosen:
                if t not in agent_tasks:
                    agent_tasks.append(t)
                if len(agent_tasks) >= args.gemma_limit:
                    break
        print(f"agent probe n={len(agent_tasks)} model={args.model}", flush=True)
        for task in agent_tasks:
            row = probe_agent(task, args.model)
            agent_rows.append(row)
            print(
                f"agent {row['instance_id']} patch={row['agent_patch']} "
                f"resolve={row['agent_resolve']} ax={row['agent_axiology_ok']} "
                f"err={row['error']}",
                flush=True,
            )

    summary = {
        "n_gold": len(gold_rows),
        "gold_resolve": sum(1 for r in gold_rows if r["gold_resolve"]),
        "fail_baseline_ok": sum(1 for r in gold_rows if r["fail_baseline"]),
        "n_agent": len(agent_rows),
        "agent_patch": sum(1 for r in agent_rows if r["agent_patch"]),
        "agent_resolve": sum(1 for r in agent_rows if r["agent_resolve"]),
        "agent_axiology_ok": sum(1 for r in agent_rows if r["agent_axiology_ok"]),
        "model": args.model if args.with_gemma else None,
        "wheels_count": len(list(WHEELS.glob("*.whl"))),
        "docker_image": DOCKER_IMAGE,
        "note": (
            "Local wheel-backed pytest resolve inside python:3.13-slim. "
            "Not the official swegemma Docker verifier."
        ),
        "gold_rows": gold_rows,
        "agent_rows": agent_rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {k: v for k, v in summary.items() if k not in {"gold_rows", "agent_rows"}},
            indent=2,
        )
    )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
