# MOEPA: Gemma 4 Developer Agent Paper Track

**Working title:** Deterministic Cognitive Governance for Offline Software Engineering Agents: The MOEPA 5-Layer Architecture on Directed AST Multigraphs

**Deadline:** November 12, 2026 · 11:59 PM UTC  
**Competition:** [gemma-4-developer-agent-paper](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper)  
**Public code:** https://github.com/PhilipAsiala/moepa-gemma4-agent

## Idea in one line

Wrap a small open model (Gemma 4) in a five-layer cognitive governance stack—**Metrology, Ontology, Epistemology, Praxeology, Axiology**—so offline agents can navigate code graphs, propose patches, and refuse unsafe or unverified edits on consumer hardware.

## Kaggle submission kit

| Artifact | Path | Use |
|----------|------|-----|
| **Writeup (paste)** | [`paper/WRITEUP.md`](paper/WRITEUP.md) | Paper Track → Writeups → draft body → **Submit** |
| Author draft | [`paper/DRAFT.md`](paper/DRAFT.md) | Same text + HTML comments; edit here, then refresh WRITEUP |
| Public notebook scaffold | [`notebooks/moepa-graph-walkthrough.md`](notebooks/moepa-graph-walkthrough.md) | New Notebook → paste cells → Settings → **Public** |
| Measured results | [`docs/microbench-results.md`](docs/microbench-results.md) | Numbers cited in the paper |
| Raw JSON | [`outputs/`](outputs/) | Microbench / snapshot / pytest-resolve rows |
| Layer mapping | [`docs/data-substrate.md`](docs/data-substrate.md) | Competition graphs / embeddings → MOEPA layers |
| Code | [`src/moepa/`](src/moepa/) | Governance layers + Ollama client |
| Reproduce | [`scripts/`](scripts/) | `paper_microbench.py`, `snapshot_probe.py`, `pytest_resolve_probe.py` |

### Paste map

1. Paste `paper/WRITEUP.md` into the Paper Track Writeup; link this GitHub repo (+ public notebook URL once live).
2. Publish a **public** notebook from `notebooks/moepa-graph-walkthrough.ipynb` (or the `.md` scaffold). First markdown cell must link this repo. Attach competition Data (`tasks.jsonl`, `graphs/`, `embeddings/`).
3. Forum post (GitHub alone does not satisfy public-sharing rules):

```text
MOEPA — governed Gemma 4 coding agent (Paper Track)

Public repo (Apache-2.0):
https://github.com/PhilipAsiala/moepa-gemma4-agent

Public notebook (graph + embedding walkthrough):
<PASTE_NOTEBOOK_URL>

Headline public-dev numbers (see repo README / docs/microbench-results.md):
- Hunk-symbol coverage 19.2% vs 3.2% random
- Gemma 4 12B file hit 10/30 → 14/30 with capped neighborhood
- Snapshot gold apply/syntax/Axiology 91/91/90
- Local wheel-backed pytest gold resolve 16/20

Happy to answer questions on the five-layer gates (Metrology / Ontology / Epistemology / Praxeology / Axiology).
```

## Headline public-dev results

On the 129-task public set (local wheel-backed pytest gold resolve 16/20):

- Lexical seed + 1-hop call neighborhood covers a gold hunk symbol in **19.2%** of cases vs **3.2%** size-matched random.
- Axiology approves **129/129** gold diffs and rejects test-tamper / shim / empty diffs.
- Shipped 256-d embeddings are weakly discriminative (mean random-pair cosine ≈ 0.829).
- Gemma 4 12B file localization (n=30): **10/30** issue-only → **14/30** with capped neighborhood.
- Snapshot gold apply / syntax / Axiology (91 single-file tasks): **91 / 91 / 90**.

Reproduce (needs local `data/` from the main competition Data tab + optional Ollama):

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
# place tasks.jsonl, graphs/, embeddings/ [, snapshots/] under data/ (see data/README.md)
.venv/bin/python scripts/paper_microbench.py --skip-gemma
.venv/bin/python scripts/paper_microbench.py --gemma-only --large-probe --model gemma4:12b
.venv/bin/python scripts/snapshot_probe.py --limit 91
```

## Status

Paper Track companion with measured substrate, gates, localization, snapshot-apply, and local wheel-backed pytest resolve evidence. Solo entrant · Apache-2.0.

## License

Copyright 2026 Philip Asiala · **Apache License 2.0** — see [`LICENSE`](LICENSE).

## Citation

> Elan Markowitz, Bryan Perozzi, Benedek Rózemberczki, Glenn Cameron, Hadi Hemmati, Yuchen Li, Michael Galkin, Majid Farhadi, Ryan Holbrook, and Ashley Oldacre. *Google - The Gemma 4 Developer Agent Paper Track*. https://www.kaggle.com/competitions/gemma-4-developer-agent-paper, 2026. Kaggle.
