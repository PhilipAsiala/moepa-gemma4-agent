# MOEPA: Gemma 4 Developer Agent Paper Track

Research repository for **Google – The Gemma 4 Developer Agent Paper Track** on Kaggle.

**Working title:** Deterministic Cognitive Governance for Offline Software Engineering Agents: The MOEPA 5-Layer Architecture on Directed AST Multigraphs

**Deadline:** November 12, 2026 · 11:59 PM UTC  
**Competition:** [gemma-4-developer-agent-paper](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper)

## Idea in one line

Wrap a small open model (Gemma 4) in a five-layer cognitive governance stack—**Metrology, Ontology, Epistemology, Praxeology, Axiology**—so offline agents can navigate code graphs, propose patches, and refuse unsafe or unverified edits on consumer hardware.

## Start here (paper prep)

| Path | Description |
|------|-------------|
| **[`paper/DRAFT.md`](paper/DRAFT.md)** | **Canonical writeup** — edit this toward the ≤3,000-word Kaggle submission |
| [`docs/data-substrate.md`](docs/data-substrate.md) | Competition graphs / embeddings / tasks → MOEPA layers (what Ontology actually reads) |
| [`docs/execution-plan.md`](docs/execution-plan.md) | 6-day checklist (experiments → results → submit) |
| [`docs/competition-brief.md`](docs/competition-brief.md) | Rules, rubric, prizes |
| [`src/moepa/`](src/moepa/) | Layered agent skeleton (companion resource) |
| `python scripts/wordcount.py` | Word-count helper vs 3,000 limit |

## Paper Track snapshot

- **Scope:** Original, unpublished research · max **3,000 words** (Kaggle Writeup)
- **Required sections:** title + subtitle · abstract · introduction · methods/experiments · related work + citations
- **Optional:** public notebook and/or public PDF project link
- **Judging (equal weight, 0–5):** Novelty · Quality · Relevance · Verifiability · Clarity

### Prizes ($35,000)

| Award | Amount |
|-------|--------|
| Overall Best Paper | $15,000 |
| Best New Resource | $10,000 |
| Best New Application | $10,000 |

## Status

Paper skeleton and code modules are in place. **Section 3 results are TBD** until the public-task micro-benchmark runs (see execution plan).

Solo entrant · public repository (no private team sharing).

## License

Copyright 2026 Philip Asiala

Licensed under the **Apache License, Version 2.0** — see [`LICENSE`](LICENSE). This matches the Paper Track winner license type and Kaggle’s public Competition Code sharing rules (OSI-approved, commercial use allowed).

## Kaggle public sharing

Kaggle allows **public** Competition Code and requires that shared code also appear on the **competition discussion forum or notebooks** so all participants can access it. When the companion resource is ready:

1. Publish a **public Kaggle Notebook** for this competition that links this repo.
2. Post a short **forum thread** with the repo URL + notebook link.
3. Point the Writeup **Project Links** field at this GitHub repo (and notebook/PDF if used).

Do **not** privately share competition code or data outside a merged team.

## Citation

> Elan Markowitz, Bryan Perozzi, Benedek Rózemberczki, Glenn Cameron, Hadi Hemmati, Yuchen Li, Michael Galkin, Majid Farhadi, Ryan Holbrook, and Ashley Oldacre. *Google - The Gemma 4 Developer Agent Paper Track*. https://www.kaggle.com/competitions/gemma-4-developer-agent-paper, 2026. Kaggle.
