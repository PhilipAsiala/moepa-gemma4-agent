#!/usr/bin/env python3
"""Paper-track micro-benchmark.

Measures what this tree can measure without repository snapshots:

- whether the shipped 256-d embeddings separate code modules
- whether a lexical seed plus a 1-hop call neighborhood covers the gold edit
- whether Axiology approves solution diffs and rejects test / shim edits
- whether Gemma 4 12B names the gold file more often with that neighborhood

Resolve rate is intentionally not reported. Pytest needs the base commit
checked out, which belongs to the later code-track harness.

Usage:
  .venv/bin/python scripts/paper_microbench.py
  .venv/bin/python scripts/paper_microbench.py --skip-gemma
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from moepa.axiology import AxiologyPolicyGate  # noqa: E402
from moepa.metrology import MetrologyState  # noqa: E402
from moepa.ontology import OntologySubstrate  # noqa: E402

DATA = ROOT / "data"
DOCS = ROOT / "docs" / "microbench-results.md"
RAW = ROOT / "outputs" / "microbench.json"
SEED = 20261107
CONTEXT_CHARS = 5000
SNIPPET_CHARS = 700
# Default 12-task probe (paper §3). Use --gemma-per-repo to enlarge.
GEMMA_BY_REPO = {
    "encode/httpx": 1,
    "psf/requests": 3,
    "Textualize/rich": 4,
    "fastapi/fastapi": 4,
}
GEMMA_BY_REPO_LARGE = {
    "encode/httpx": 1,
    "psf/requests": 6,
    "Textualize/rich": 10,
    "fastapi/fastapi": 13,
}


def load_tasks() -> List[dict]:
    rows = []
    for line in (DATA / "tasks.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def stem_for(task: dict) -> str:
    repo = task["repo"].split("/")[-1]
    return f"{repo}_{task['base_commit']}"


def gold_files(diff: str) -> List[str]:
    return [ln[6:].strip() for ln in diff.splitlines() if ln.startswith("+++ b/")]


def file_prefix(path: str) -> str:
    rel = path.strip().replace("\\", "/")
    if rel.startswith("src/"):
        rel = rel[4:]
    if rel.endswith(".py"):
        rel = rel[:-3]
    return rel.replace("/", ".")


def covers_file(node_ids: Iterable[str], path: str) -> bool:
    prefix = file_prefix(path)
    return any(nid == prefix or nid.startswith(prefix + ".") for nid in node_ids)


def gold_hunk_symbols(diff: str) -> List[str]:
    found = []
    for line in diff.splitlines():
        match = re.search(r"^@@ .*@@\s*(?:async\s+def|def|class)\s+(\w+)", line)
        if match and match.group(1) not in found:
            found.append(match.group(1))
    return found


def covers_symbol(node_ids: Iterable[str], name: str) -> bool:
    suffix = "." + name
    return any(nid == name or nid.endswith(suffix) for nid in node_ids)


def graph_path(task: dict) -> Path:
    return DATA / "graphs" / f"{stem_for(task)}.json"


def embedding_path(task: dict) -> Path:
    return DATA / "embeddings" / f"{stem_for(task)}.npz"


def stat(values: Sequence[float]) -> dict:
    arr = np.asarray(values, dtype=np.float64)
    return {
        "n": int(arr.size),
        "mean": float(arr.mean()),
        "std": float(arr.std()),
        "p10": float(np.percentile(arr, 10)),
        "p50": float(np.percentile(arr, 50)),
        "p90": float(np.percentile(arr, 90)),
    }


def embedding_geometry(tasks: Sequence[dict], rng: random.Random, pairs: int = 200) -> dict:
    """Cosine geometry of the shipped archives. Vectors are already L2-normalized."""
    seen = set()
    random_cos: List[float] = []
    same_cos: List[float] = []
    cross_cos: List[float] = []
    for task in tasks:
        stem = stem_for(task)
        if stem in seen or not embedding_path(task).exists():
            continue
        seen.add(stem)
        ont = OntologySubstrate(graph_path(task), embedding_path(task))
        emb = ont.embeddings
        assert emb is not None
        parents = [nid.rsplit(".", 1)[0] for nid in ont.node_ids]
        n = len(ont.node_ids)
        if n < 2:
            continue
        for _ in range(pairs):
            i = rng.randrange(n)
            j = rng.randrange(n)
            if i == j:
                continue
            cosine = float(emb[i] @ emb[j])
            random_cos.append(cosine)
            if parents[i] == parents[j]:
                same_cos.append(cosine)
            else:
                cross_cos.append(cosine)
        del ont
    return {
        "snapshots": len(seen),
        "random_pair": stat(random_cos),
        "same_parent": stat(same_cos),
        "cross_parent": stat(cross_cos),
    }


def neighborhood(task: dict, rng: random.Random, trials: int = 5) -> dict:
    ont = OntologySubstrate(graph_path(task))
    files = gold_files(task["patch"])
    symbols = gold_hunk_symbols(task["patch"])
    seeds = ont.seed_symbols_from_text(task["problem_statement"], limit=8)
    ctx = ont.build_bounded_context(seeds, hops=1)
    lex_ids = list(ctx)
    file_hits = sum(covers_file(lex_ids, path) for path in files)
    sym_hits = sum(covers_symbol(lex_ids, name) for name in symbols)
    rand_file = []
    rand_sym = []
    rand_task_hits = []
    k = max(1, len(seeds))
    for _ in range(trials):
        draw = rng.sample(ont.node_ids, k=min(k, len(ont.node_ids)))
        rand_ctx = ont.build_bounded_context(draw, hops=1)
        rand_ids = list(rand_ctx)
        file_hit_n = sum(covers_file(rand_ids, path) for path in files)
        rand_file.append(file_hit_n / max(1, len(files)))
        rand_task_hits.append(1.0 if file_hit_n else 0.0)
        if symbols:
            rand_sym.append(sum(covers_symbol(rand_ids, name) for name in symbols) / len(symbols))
    chars = sum(len(text) for text in ctx.values())
    return {
        "instance_id": task["instance_id"],
        "repo": task["repo"],
        "n_gold_files": len(files),
        "n_gold_symbols": len(symbols),
        "n_seeds": len(seeds),
        "n_ctx": len(ctx),
        "ctx_chars": chars,
        "lex_file_hits": file_hits,
        "lex_symbol_hits": sym_hits,
        "rand_file_recall": float(np.mean(rand_file)) if rand_file else 0.0,
        "rand_task_hit_rate": float(np.mean(rand_task_hits)) if rand_task_hits else 0.0,
        "rand_symbol_recall": float(np.mean(rand_sym)) if rand_sym else None,
        "ctx": ctx,
        "seeds": seeds,
        "gold_files": files,
    }


def axiology_sweep(tasks: Sequence[dict]) -> dict:
    gold_ok = 0
    tamper_rejected = 0
    shim_rejected = 0
    empty_rejected = 0
    for task in tasks:
        diff = task["patch"]
        ok, _ = AxiologyPolicyGate.evaluate_patch_policy(diff)
        gold_ok += int(ok)
        tampered = diff + "\n+++ b/tests/test_moepa_tamper.py\n"
        bad, _ = AxiologyPolicyGate.evaluate_patch_policy(tampered)
        tamper_rejected += int(not bad)
        shimmed = diff + "\n+++ b/imp.py\n"
        shim_ok, _ = AxiologyPolicyGate.evaluate_patch_policy(shimmed)
        shim_rejected += int(not shim_ok)
        empty_ok, _ = AxiologyPolicyGate.evaluate_patch_policy("")
        empty_rejected += int(not empty_ok)
    n = len(tasks)
    return {
        "n": n,
        "gold_approved": gold_ok,
        "test_tamper_rejected": tamper_rejected,
        "shim_rejected": shim_rejected,
        "empty_rejected": empty_rejected,
    }


def metrology_trace() -> dict:
    state = MetrologyState(task_id="trace")
    radii = [state.ast_hop_radius]
    stagnating = []
    for _ in range(4):
        stagnating.append(state.record_and_check_stagnation("SYNTAX_FAULT"))
        radii.append(state.ast_hop_radius)
    varied = MetrologyState(task_id="varied")
    varied_flags = [
        varied.record_and_check_stagnation(f"FAULT_{i}") for i in range(3)
    ]
    return {
        "repeated_signature_stagnating": stagnating,
        "repeated_signature_hop_radius": radii,
        "exhausted_after_repeated": state.budget_exhausted(),
        "varied_signature_stagnating": varied_flags,
        "varied_hop_radius": varied.ast_hop_radius,
    }


def pack_context(ctx: Dict[str, str], seeds: Sequence[str], budget: int = CONTEXT_CHARS) -> str:
    ordered = [nid for nid in seeds if nid in ctx]
    ordered.extend(nid for nid in ctx if nid not in ordered)
    parts = []
    used = 0
    for nid in ordered:
        snippet = ctx[nid][:SNIPPET_CHARS]
        piece = f"### {nid}\n{snippet}\n"
        if used + len(piece) > budget:
            break
        parts.append(piece)
        used += len(piece)
    return "".join(parts)


def select_gemma_tasks(
    tasks: Sequence[dict], quotas: Optional[Dict[str, int]] = None
) -> List[dict]:
    chosen = []
    for repo, count in (quotas or GEMMA_BY_REPO).items():
        pool = [task for task in tasks if task["repo"] == repo]
        singles = [task for task in pool if len(gold_files(task["patch"])) == 1]
        singles.sort(key=lambda task: task["instance_id"])
        take = singles[:count]
        if len(take) < count:
            rest = [task for task in pool if task not in take]
            rest.sort(key=lambda task: task["instance_id"])
            take.extend(rest[: count - len(take)])
        chosen.extend(take)
    return chosen


def _post_chat(payload: dict) -> dict:
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ollama_json(prompt: str, model: str = "gemma4:12b") -> dict:
    payload = {
        "model": model,
        "stream": False,
        "think": False,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You localize a bug in a repository. "
                    "Reply with one JSON object and no other text. "
                    'Schema: {"files": ["relative/path.py"], "abstain": false}. '
                    "Use repository-relative paths. "
                    "If you cannot tell which file to edit, set abstain to true and files to []."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "options": {"temperature": 0.2, "num_ctx": 4096, "num_predict": 256},
    }
    # model is closed over by callers via gemma_condition(..., model=)
    started = time.monotonic()
    try:
        body = _post_chat(payload)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        if exc.code == 400 and "think" in detail:
            payload.pop("think", None)
            body = _post_chat(payload)
        else:
            raise RuntimeError(f"Ollama HTTP {exc.code}: {detail}") from exc
    elapsed = time.monotonic() - started
    message = body.get("message") or {}
    text = (message.get("content") or message.get("thinking") or "").strip()
    return {"seconds": elapsed, "text": text, "parsed": parse_files(text)}


def parse_files(text: str) -> Optional[dict]:
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return None
    try:
        obj = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    files = obj.get("files")
    if not isinstance(files, list):
        return None
    return {
        "files": [str(item) for item in files],
        "abstain": bool(obj.get("abstain")),
    }


def path_matches(pred: str, gold: str) -> bool:
    """True when two paths name the same file, ignoring a leading src/ or ./."""
    left = pred.strip().replace("\\", "/").lstrip("./")
    right = gold.strip().replace("\\", "/")
    if left == right or left.endswith("/" + right) or right.endswith("/" + left):
        return True
    return file_prefix(left) == file_prefix(right)


def gemma_condition(
    task: dict,
    neighborhood_row: dict,
    use_ontology: bool,
    model: str = "gemma4:12b",
) -> dict:
    issue = task["problem_statement"][:4000]
    prompt = f"Issue:\n{issue}\n"
    if use_ontology:
        packed = pack_context(neighborhood_row["ctx"], neighborhood_row["seeds"])
        prompt += f"\nCode neighborhood:\n{packed}\n"
    prompt += "\nWhich files should be edited?\n"
    try:
        result = ollama_json(prompt, model=model)
        error = None
    except (urllib.error.URLError, RuntimeError, TimeoutError) as exc:
        return {
            "instance_id": task["instance_id"],
            "ontology": use_ontology,
            "error": str(exc),
            "hit": False,
            "abstain": False,
            "parsed": False,
            "seconds": None,
            "files": [],
        }
    parsed = result["parsed"]
    files = parsed["files"] if parsed else []
    abstain = bool(parsed["abstain"]) if parsed else False
    gold = neighborhood_row["gold_files"]
    hit = any(path_matches(pred, truth) for pred in files for truth in gold)
    return {
        "instance_id": task["instance_id"],
        "repo": task["repo"],
        "ontology": use_ontology,
        "error": error,
        "hit": hit and not abstain,
        "abstain": abstain,
        "parsed": parsed is not None,
        "seconds": result["seconds"],
        "files": files,
        "gold_files": gold,
        "text": result["text"][:500],
    }


def pct(num: int, den: int) -> str:
    if den == 0:
        return "n/a"
    return f"{num}/{den} ({100.0 * num / den:.1f}%)"


def render(report: dict) -> str:
    loc = report["localization"]
    emb = report["embeddings"]
    ax = report["axiology"]
    met = report["metrology"]
    lines = [
        "# Paper micro-benchmark",
        "",
        "Measured from `scripts/paper_microbench.py` on the public development set.",
        "Repository snapshots were not checked out, so this file does not report a pytest resolve rate.",
        "",
        "## Embeddings",
        "",
        f"Snapshots: {emb['snapshots']}. "
        f"Random-pair cosine mean {emb['random_pair']['mean']:.3f} "
        f"(p10 {emb['random_pair']['p10']:.3f}, p90 {emb['random_pair']['p90']:.3f}). "
        f"Same-parent mean {emb['same_parent']['mean']:.3f}. "
        f"Cross-parent mean {emb['cross_parent']['mean']:.3f}.",
        "",
        "## Ontology localization",
        "",
        f"Tasks: {loc['n_tasks']}. Gold files: {loc['n_files']}.",
        f"Lexical seed + 1-hop file recall: {pct(loc['lex_file_hits'], loc['n_files'])}.",
        f"Size-matched random neighborhood file recall: {loc['rand_file_recall']:.3f}.",
        f"Task-level lexical coverage (at least one gold file): {pct(loc['lex_tasks'], loc['n_tasks'])}.",
        f"Random task-level coverage, mean over trials: {loc['rand_task_rate']:.3f}.",
        f"Hunk-symbol recall: {pct(loc['lex_symbol_hits'], loc['n_symbols'])} "
        f"versus random {loc['rand_symbol_recall']:.3f}.",
        f"Neighborhood size: median {loc['ctx_chars']['p50']:.0f} chars, "
        f"p90 {loc['ctx_chars']['p90']:.0f}. "
        f"Tasks over the {CONTEXT_CHARS}-char prompt cap: {loc['over_cap']}.",
        "",
        "## Gates",
        "",
        f"Axiology approved {ax['gold_approved']}/{ax['n']} gold solution diffs.",
        f"Rejected test-file tamper {ax['test_tamper_rejected']}/{ax['n']}, "
        f"protected shim {ax['shim_rejected']}/{ax['n']}, "
        f"empty diff {ax['empty_rejected']}/{ax['n']}.",
        f"Metrology on a repeated diagnostic: stagnating={met['repeated_signature_stagnating']}, "
        f"hop radius={met['repeated_signature_hop_radius']}, "
        f"budget exhausted={met['exhausted_after_repeated']}. "
        f"Varied diagnostics did not stagnate ({met['varied_signature_stagnating']}) "
        f"and left hop radius at {met['varied_hop_radius']}.",
        "",
    ]
    gemma = report.get("gemma")
    if gemma:
        lines.extend(
            [
                "## Gemma 4 12B file localization",
                "",
                f"Model `{gemma['model']}` on `127.0.0.1:11434`, think disabled, "
                f"context 4096, {gemma['n']} public tasks.",
                f"Issue text only: file hit {pct(gemma['base_hits'], gemma['n'])}, "
                f"abstain {gemma['base_abstain']}, parse failures {gemma['base_unparsed']}, "
                f"mean {gemma['base_seconds']:.1f}s.",
                f"Issue plus capped neighborhood: file hit {pct(gemma['ont_hits'], gemma['n'])}, "
                f"abstain {gemma['ont_abstain']}, parse failures {gemma['ont_unparsed']}, "
                f"mean {gemma['ont_seconds']:.1f}s.",
                "",
                "| Task | Repo | Gold file | Issue only | With neighborhood |",
                "|---|---|---|---|---|",
            ]
        )
        for row in gemma["rows"]:
            lines.append(
                f"| `{row['instance_id']}` | {row['repo'].split('/')[-1]} | "
                f"`{row['gold']}` | {row['base']} | {row['ont']} |"
            )
        lines.append("")
    for key, title in (
        ("gemma_26b", "Gemma 4 26B file localization (comparison)"),
        ("gemma_31b", "Gemma 4 31B file localization (comparison)"),
    ):
        alt = report.get(key)
        if not alt:
            continue
        lines.extend(
            [
                f"## {title}",
                "",
                f"Model `{alt['model']}` on `127.0.0.1:11434`, think disabled, "
                f"context 4096, {alt['n']} public tasks.",
                f"Issue text only: file hit {pct(alt['base_hits'], alt['n'])}, "
                f"abstain {alt.get('base_abstain', 0)}, parse failures {alt.get('base_unparsed', 0)}, "
                f"mean {alt['base_seconds']:.1f}s.",
                f"Issue plus capped neighborhood: file hit {pct(alt['ont_hits'], alt['n'])}, "
                f"abstain {alt.get('ont_abstain', 0)}, parse failures {alt.get('ont_unparsed', 0)}, "
                f"mean {alt['ont_seconds']:.1f}s.",
                "",
            ]
        )
    return "\n".join(lines)


def summarize_localization(rows: Sequence[dict]) -> dict:
    n_files = sum(row["n_gold_files"] for row in rows)
    n_symbols = sum(row["n_gold_symbols"] for row in rows)
    lex_tasks = sum(row["lex_file_hits"] > 0 for row in rows)
    rand_task = [row["rand_task_hit_rate"] for row in rows]
    sym_rand = [
        row["rand_symbol_recall"]
        for row in rows
        if row["rand_symbol_recall"] is not None
    ]
    return {
        "n_tasks": len(rows),
        "n_files": n_files,
        "n_symbols": n_symbols,
        "lex_file_hits": sum(row["lex_file_hits"] for row in rows),
        "lex_symbol_hits": sum(row["lex_symbol_hits"] for row in rows),
        "lex_tasks": lex_tasks,
        "rand_file_recall": float(
            np.mean([row["rand_file_recall"] for row in rows])
        ),
        "rand_task_rate": float(np.mean(rand_task)) if rand_task else 0.0,
        "rand_symbol_recall": float(np.mean(sym_rand)) if sym_rand else 0.0,
        "ctx_chars": stat([row["ctx_chars"] for row in rows]),
        "over_cap": sum(row["ctx_chars"] > CONTEXT_CHARS for row in rows),
        "mean_seeds": float(np.mean([row["n_seeds"] for row in rows])),
        "mean_ctx_nodes": float(np.mean([row["n_ctx"] for row in rows])),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-gemma", action="store_true")
    parser.add_argument("--gemma-only", action="store_true")
    parser.add_argument("--model", default="gemma4:12b")
    parser.add_argument(
        "--large-probe",
        action="store_true",
        help="Use GEMMA_BY_REPO_LARGE (~30 tasks) instead of the 12-task paper probe",
    )
    args = parser.parse_args()
    rng = random.Random(SEED)
    tasks = load_tasks()
    RAW.parent.mkdir(parents=True, exist_ok=True)

    if args.gemma_only and RAW.exists():
        report = json.loads(RAW.read_text(encoding="utf-8"))
        loc_rows_by_id = {row["instance_id"]: row for row in report["localization_rows"]}
    else:
        print(f"tasks {len(tasks)}", flush=True)
        print("embedding geometry...", flush=True)
        embeddings = embedding_geometry(tasks, rng)
        print("localization...", flush=True)
        loc_rows = [neighborhood(task, rng) for task in tasks]
        report = {
            "seed": SEED,
            "n_tasks": len(tasks),
            "embeddings": embeddings,
            "localization": summarize_localization(loc_rows),
            "localization_rows": [
                {key: value for key, value in row.items() if key != "ctx"}
                for row in loc_rows
            ],
            "axiology": axiology_sweep(tasks),
            "metrology": metrology_trace(),
        }
        # Keep the in-memory contexts only for the Gemma subset.
        report["_ctx"] = {
            row["instance_id"]: {"ctx": row["ctx"], "seeds": row["seeds"], "gold_files": row["gold_files"]}
            for row in loc_rows
        }
        loc_rows_by_id = report["_ctx"]
        print(json.dumps({k: report[k] for k in ("embeddings", "localization", "axiology", "metrology")}, indent=2))

    if not args.skip_gemma:
        quotas = GEMMA_BY_REPO_LARGE if args.large_probe else GEMMA_BY_REPO
        chosen = select_gemma_tasks(tasks, quotas=quotas)
        print(
            f"gemma model={args.model} tasks={[task['instance_id'] for task in chosen]}",
            flush=True,
        )
        details = []
        for task in chosen:
            row = loc_rows_by_id[task["instance_id"]]
            if "ctx" not in row:
                fresh = neighborhood(task, rng, trials=1)
                row = fresh
            base = gemma_condition(task, row, use_ontology=False, model=args.model)
            ont = gemma_condition(task, row, use_ontology=True, model=args.model)
            print(
                f"{task['instance_id']} base={base['hit']}/{base['parsed']} "
                f"ont={ont['hit']}/{ont['parsed']} "
                f"{base.get('seconds')} {ont.get('seconds')}",
                flush=True,
            )
            details.append((base, ont))
        def hits(side: int) -> int:
            return sum(pair[side]["hit"] for pair in details)

        def seconds(side: int) -> float:
            vals = [pair[side]["seconds"] for pair in details if pair[side]["seconds"]]
            return float(np.mean(vals)) if vals else 0.0

        gemma_block = {
            "model": args.model,
            "n": len(details),
            "base_hits": hits(0),
            "ont_hits": hits(1),
            "base_abstain": sum(pair[0]["abstain"] for pair in details),
            "ont_abstain": sum(pair[1]["abstain"] for pair in details),
            "base_unparsed": sum(not pair[0]["parsed"] for pair in details),
            "ont_unparsed": sum(not pair[1]["parsed"] for pair in details),
            "base_seconds": seconds(0),
            "ont_seconds": seconds(1),
            "rows": [
                {
                    "instance_id": pair[0]["instance_id"],
                    "repo": pair[0].get("repo", ""),
                    "gold": ", ".join(pair[0].get("gold_files") or []),
                    "base": ", ".join(pair[0]["files"]) or ("abstain" if pair[0]["abstain"] else "unparsed"),
                    "ont": ", ".join(pair[1]["files"]) or ("abstain" if pair[1]["abstain"] else "unparsed"),
                    "base_hit": pair[0]["hit"],
                    "ont_hit": pair[1]["hit"],
                }
                for pair in details
            ],
            "details": details,
        }
        # Keep the primary paper probe under `gemma`; stash other models beside it.
        if args.model == "gemma4:12b" or "gemma" not in report:
            report["gemma"] = gemma_block
        else:
            key = "gemma_" + args.model.split(":")[-1].replace(".", "_")
            report[key] = gemma_block


    report.pop("_ctx", None)
    # Drop bulky contexts if a gemma-only reload stored them inside localization rows.
    RAW.write_text(json.dumps(report, indent=2), encoding="utf-8")
    DOCS.write_text(render(report), encoding="utf-8")
    print(f"wrote {DOCS}", flush=True)


if __name__ == "__main__":
    main()
