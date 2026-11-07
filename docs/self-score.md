# Paper Track self-score (working)

Rubric axes 0–5. Update before Submit. Scores below are honest against current public evidence (`paper/WRITEUP.md`, `docs/microbench-results.md`, `outputs/pytest_resolve.json`).

| Axis | Score | Notes |
|------|------:|-------|
| **Novelty** | 3.5 | Layered governance framing on competition graphs is clear; not a new localization algorithm. Strongest as *application* of AST multigraph + gates. |
| **Quality** | 4 | Measured numbers, ablations (random neighborhood, issue-only vs ontology, syntax-only vs pytest gate), limitations stated. Agent resolve still 0/3. |
| **Relevance** | 4.5 | Directly targets offline Gemma 4 SWE agents on the provided substrate. |
| **Verifiability** | 4 | Public Apache-2.0 repo, scripts, raw JSON, snapshot + wheel probes. Official swegemma Docker verifier not claimed. |
| **Clarity** | 4 | Method figure + table; word count under 3k. Abstract/Conclusion jargon trimmed (Clarity pass). |

**Target awards**

| Award | Fit now | Gap |
|-------|---------|-----|
| Overall Best Paper | Competitive if clarity holds | Need public notebook + writeup submitted early |
| Best New Application | Strong | Keep “governance of small models on graphs” as the hook |
| Best New Resource | Incomplete until notebook is **public** on Kaggle | Paste [`notebooks/moepa-graph-walkthrough.md`](../notebooks/moepa-graph-walkthrough.md) |

Clarity pass on `paper/WRITEUP.md` Abstract/Conclusion is done. Revisit scores after the Kaggle Notebook is live.
