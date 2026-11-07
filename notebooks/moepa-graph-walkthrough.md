# MOEPA graph + embedding walkthrough (public notebook scaffold)

**Repo:** https://github.com/PhilipAsiala/moepa-gemma4-agent  
**Purpose:** Best New Resource — show how Ontology loads one public AST multigraph and aligned 256-d embeddings, then builds a bounded neighborhood.

Paste this Markdown into a **public** Kaggle Notebook (or open it as cells). Competition assets are **not** in git; attach them from the Data tab or place them under `data/` when running locally.

```text
Expected layout (when present)
  data/tasks.jsonl
  data/graphs/<repo>_<base_commit>.json   # or task-named hardlinks
  data/embeddings/<repo>_<base_commit>.npz
```

If those paths are missing, cells stop with a clear placeholder message instead of inventing numbers.

---

## 0. Install + path bootstrap

```python
# Kaggle: !pip install -q numpy
# Local: pip install -r requirements.txt  (from repo root)

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

# Repo root: Kaggle /working clone, or notebook next to repo
CANDIDATES = [
    Path("/kaggle/working/moepa-gemma4-agent"),
    Path.cwd(),
    Path.cwd().parent,
]
ROOT = next((p for p in CANDIDATES if (p / "src" / "moepa").is_dir()), Path.cwd())
sys.path.insert(0, str(ROOT / "src"))

DATA = ROOT / "data"
# Kaggle Dataset mount (adjust name if your attached dataset differs)
KAGGLE_INPUT = Path("/kaggle/input")
if not (DATA / "graphs").exists() and KAGGLE_INPUT.exists():
    for child in KAGGLE_INPUT.iterdir():
        if (child / "graphs").exists() or (child / "tasks.jsonl").exists():
            DATA = child
            break

print("ROOT:", ROOT)
print("DATA:", DATA)
```

---

## 1. Detect competition data (or stop cleanly)

```python
graphs_dir = DATA / "graphs"
emb_dir = DATA / "embeddings"
tasks_path = DATA / "tasks.jsonl"

missing = [str(p) for p in (graphs_dir, emb_dir, tasks_path) if not p.exists()]
if missing:
    print(
        "PLACEHOLDER — competition data absent.\n"
        "Attach the Gemma 4 Developer Agent public assets (tasks.jsonl, graphs/, embeddings/)\n"
        "from the Kaggle Data tab, or copy them into data/ locally.\n"
        "Missing:\n  - " + "\n  - ".join(missing)
    )
    DATA_OK = False
else:
    DATA_OK = True
    print(f"Found {len(list(graphs_dir.glob('*.json')))} graphs, "
          f"{len(list(emb_dir.glob('*.npz')))} embedding archives, "
          f"tasks at {tasks_path}")
```

---

## 2. Pick one public task + matching graph / embedding pair

```python
if not DATA_OK:
    raise SystemExit("Skip remaining cells until data is present.")

# First task with a resolvable base_commit pair (schema may vary slightly)
task = None
with tasks_path.open(encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        task = json.loads(line)
        break

assert task is not None, "tasks.jsonl is empty"
instance_id = task.get("instance_id") or task.get("id") or task.get("task_id")
repo = (task.get("repo") or task.get("repo_name") or "").replace("/", "__")
base = task.get("base_commit") or task.get("base_sha") or ""
problem = task.get("problem_statement") or task.get("issue") or ""

print("task:", instance_id)
print("repo / base_commit:", repo, base[:12] if base else "(missing)")

# Prefer commit-named files; fall back to any single pair for a smoke walk
graph_path = None
emb_path = None
if repo and base:
    for gname in (f"{repo}_{base}.json", f"{base}.json", f"{instance_id}.json"):
        cand = graphs_dir / gname
        if cand.exists():
            graph_path = cand
            break
    for ename in (f"{repo}_{base}.npz", f"{base}.npz", f"{instance_id}.npz"):
        cand = emb_dir / ename
        if cand.exists():
            emb_path = cand
            break

if graph_path is None:
    graph_path = next(graphs_dir.glob("*.json"), None)
if emb_path is None and graph_path is not None:
    stem = graph_path.stem
    cand = emb_dir / f"{stem}.npz"
    emb_path = cand if cand.exists() else next(emb_dir.glob("*.npz"), None)

if graph_path is None or emb_path is None:
    print(
        "PLACEHOLDER — could not pair graph JSON with embeddings .npz for this task.\n"
        f"  graph_path={graph_path}\n  emb_path={emb_path}\n"
        "List data/graphs and data/embeddings and set graph_path / emb_path manually."
    )
    raise SystemExit("Need one graph + one embedding archive.")

print("graph:", graph_path.name)
print("embeddings:", emb_path.name)
```

---

## 3. Load Ontology substrate (graph + 256-d vectors)

```python
from moepa.ontology import OntologySubstrate

onto = OntologySubstrate(graph_path, emb_path)
print(f"nodes={len(onto.node_ids)} edges={len(onto.edges)}")
print(f"embeddings shape={None if onto.embeddings is None else onto.embeddings.shape}")

# Spot-check: random-pair cosine (weakly discriminative on public set; see paper §3)
if onto.embeddings is not None and len(onto.node_ids) >= 4:
    rng = np.random.default_rng(0)
    idx = rng.choice(len(onto.node_ids), size=4, replace=False)
    a, b = onto.embeddings[idx[0]], onto.embeddings[idx[1]]
    print("example cosine(random pair):", float(np.dot(a, b)))
```

---

## 4. Lexical seeds → 1-hop bounded context

```python
seeds = onto.seed_symbols_from_text(problem or " ", limit=8)
print(f"lexical seeds ({len(seeds)}):", seeds[:5])

if not seeds and onto.node_ids:
    # PLACEHOLDER fallback so the walkthrough still shows a neighborhood when
    # the issue text has no name overlap with graph ids.
    seeds = onto.node_ids[:1]
    print("PLACEHOLDER seed (first node id) — issue text had no lexical hits:", seeds)

ctx = onto.build_bounded_context(seeds, hops=1)
print(f"bounded context symbols: {len(ctx)}")
for i, (sym, text) in enumerate(ctx.items()):
    if i >= 3:
        break
    snippet = (text or "").replace("\n", " ")[:160]
    print(f"  - {sym}: {snippet!r}...")
```

---

## 5. Optional: dense seed ranking (needs a query vector)

```python
# The competition sandbox exposes search_similar_code with a query encoder that
# matches this 256-d space. This notebook does NOT ship that encoder.
# When you have a float32[256] query vector q (L2-normalized), rank seeds with:

# ranked = onto.rank_seeds_by_embedding(q, top_k=8)
# print(ranked)

print(
    "PLACEHOLDER — skip embedding retrieval until a same-space query vector is available.\n"
    "Lexical seeds (cell 4) are the offline fallback used by the agent skeleton."
)
```

---

## 6. Link back to the paper + gates

- Method: Ontology layer in `paper/DRAFT.md` §2.2  
- Measured neighborhood / gate numbers: `paper/DRAFT.md` §3 (do not invent new stats here)  
- Code: `src/moepa/ontology.py`, agent loop in `src/moepa/agent.py`  
- Datasheet: `docs/data-substrate.md`

When publishing on Kaggle: set the notebook **public**, link this GitHub repo in the notebook description, and add the notebook URL under Writeup Project Links.
