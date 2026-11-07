# MOEPA: Gemma 4 Developer Agent Paper Track

Research repository for **Google – The Gemma 4 Developer Agent Paper Track** on Kaggle.

**Working title:** Deterministic Cognitive Governance for Offline Software Engineering Agents: The MOEPA 5-Layer Architecture on Directed AST Multigraphs

**Deadline:** November 12, 2026 · 11:59 PM UTC  
**Competition:** [gemma-4-developer-agent-paper](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper)  
**Public code:** https://github.com/PhilipAsiala/moepa-gemma4-agent

## Idea in one line

Wrap a small open model (Gemma 4) in a five-layer cognitive governance stack—**Metrology, Ontology, Epistemology, Praxeology, Axiology**—so offline agents can navigate code graphs, propose patches, and refuse unsafe or unverified edits on consumer hardware.

## Start here

| Path | Description |
|------|-------------|
| **[`paper/DRAFT.md`](paper/DRAFT.md)** | Canonical writeup (edit this) |
| [`paper/WRITEUP.md`](paper/WRITEUP.md) | Kaggle-ready paste (no HTML comments) |
| [`docs/microbench-results.md`](docs/microbench-results.md) | Measured results summary |
| [`outputs/microbench.json`](outputs/microbench.json) | Raw microbench rows |
| [`scripts/paper_microbench.py`](scripts/paper_microbench.py) | Reproduce substrate / gate / localization probes |
| [`docs/data-substrate.md`](docs/data-substrate.md) | Competition graphs / embeddings → MOEPA layers |
| [`src/moepa/`](src/moepa/) | Layered agent + Ollama client |

## Headline public-dev results

On the 129-task public set (no pytest resolve rate yet):

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

Paper Track companion with measured substrate, gates, localization, and snapshot-apply evidence. Solo entrant · public Apache-2.0 repo. Fail-to-pass pytest resolve remains future work (competition wheels/sandbox).

## License

Copyright 2026 Philip Asiala · **Apache License 2.0** — see [`LICENSE`](LICENSE).

## Kaggle public sharing

1. Publish a public Kaggle Notebook linking this repo.  
2. Forum post with repo + notebook.  
3. Writeup Project Links → this GitHub URL.

## Citation

> Elan Markowitz, Bryan Perozzi, Benedek Rózemberczki, Glenn Cameron, Hadi Hemmati, Yuchen Li, Michael Galkin, Majid Farhadi, Ryan Holbrook, and Ashley Oldacre. *Google - The Gemma 4 Developer Agent Paper Track*. https://www.kaggle.com/competitions/gemma-4-developer-agent-paper, 2026. Kaggle.
