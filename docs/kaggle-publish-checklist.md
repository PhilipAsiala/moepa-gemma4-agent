# Kaggle publish checklist (Paper Track)

Do these in the Kaggle UI (phone or desktop). GitHub alone does **not** satisfy public-sharing rules.

## What to paste where (one screen)

| Paste this | Where on Kaggle |
| --- | --- |
| `paper/WRITEUP.md` | Paper Track → **Writeups** → draft body |
| `notebooks/moepa-graph-walkthrough.md` | **New Notebook** → cells (then Settings → Public) |
| `https://github.com/PhilipAsiala/moepa-gemma4-agent` | Notebook description + Writeup **Project Links** |
| Forum block in §3 below | Competition **Discussion** (swap in notebook URL after publish) |
| Public notebook URL (after you publish it) | Writeup **Project Links** + forum `<PASTE_NOTEBOOK_URL>` |

**Submit** the Writeup by **Thu Nov 12, 2026 · 11:59 PM UTC** — drafts do not count. Clarity pass on WRITEUP is done in-repo; refresh the draft body after merging this polish.

## 1. Public notebook

1. New Notebook → paste cells from [`../notebooks/moepa-graph-walkthrough.md`](../notebooks/moepa-graph-walkthrough.md).
2. Add Data: competition **gemma-4-developer-agent** public files (or attach `tasks.jsonl` + one graph/embedding pair).
3. Settings → **Public**.
4. Title suggestion: `MOEPA graph + embedding walkthrough`
5. First markdown cell must link: https://github.com/PhilipAsiala/moepa-gemma4-agent
6. Copy the notebook URL into Writeup **Project Links**.

## 2. Writeup draft (tie-break: earlier entry wins ties)

1. Open [Paper Track](https://www.kaggle.com/competitions/gemma-4-developer-agent-paper) → Writeups.
2. Create/edit draft; paste `paper/WRITEUP.md`.
3. Project Links → GitHub repo + public notebook (+ PDF optional).
4. Paste the latest `paper/WRITEUP.md` (Clarity pass done in-repo); **Submit** by Thu Nov 12 23:59 UTC (drafts do not count).

## 3. Forum post (paste)

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

## 4. Rules / identity

- [ ] Accept Paper Track rules (and Main if also entering)
- [ ] Kaggle identity verified if required for prizes
