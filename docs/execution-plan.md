# 6-day execution plan (Paper Track)

**Hard deadline:** Thursday, Nov 12, 2026 · 11:59 PM UTC  
**Working paper:** [`../paper/DRAFT.md`](../paper/DRAFT.md)  
**Code:** [`../src/moepa/`](../src/moepa/)

## Prize targeting

Aim to be competitive for all three Paper Track awards by shipping:

1. **Overall Best Paper** — clear method + ablation + honest limitations (`paper/DRAFT.md`)
2. **Best New Application** — MOEPA as a governance application of AST multigraphs + embeddings
3. **Best New Resource** — public repo + optional Kaggle notebook demonstrating graph/embedding traversal

## Checklist

### Today (Fri Nov 6)

- [ ] Accept rules on Paper Track (and Main Competition if also entering)
- [x] Repo public with paper skeleton + code modules
- [x] Apache 2.0 `LICENSE` (winner license type + public code sharing)
- [ ] Join / verify identity on Kaggle if not done
- [ ] Create draft Kaggle Writeup early (tie-break is first entry among equal scores)
- [ ] When sharing code: mirror on competition **forum and/or public notebook** (GitHub alone is not enough under Kaggle public-sharing rules)

### Sat–Mon (Nov 7–9) — evidence

- [x] Download public assets (`tasks.jsonl`, graphs, embeddings, snapshots) into `data/`
- [x] Wire Gemma 4 into `MOEPAGemmaAgent._synthesize_edit` (Ollama / B70)
- [x] Run micro-benchmark + 30-task Gemma localization + snapshot gold-apply probe
- [x] Fill Section 3 table + headline Abstract / Conclusion sentences in `paper/DRAFT.md`
- [x] Optional: competition wheels + `python:3.13-slim` local pytest resolve probe (`scripts/pytest_resolve_probe.py`)

### Tue–Wed (Nov 10–11) — polish

- [x] Trim writeup to ≤ **3,000 words** (`python scripts/wordcount.py`) — WRITEUP/DRAFT both **2472** after Clarity pass (Abstract/Conclusion jargon shortened; §3 numbers unchanged)
- [ ] Expand Related Work only with papers you actually engaged
- [x] Scaffold Kaggle-notebook Markdown: [`../notebooks/moepa-graph-walkthrough.md`](../notebooks/moepa-graph-walkthrough.md) (graph + embedding load; placeholders when `data/` absent)
- [ ] Publish **public** Kaggle Notebook from that scaffold linking https://github.com/PhilipAsiala/moepa-gemma4-agent — steps in [`kaggle-publish-checklist.md`](kaggle-publish-checklist.md)
- [x] Android cloud-agent control notes: [`android-cloud.md`](android-cloud.md) (cursor.com/agents on Chrome; GPU/data stay on workstation)
- [ ] Forum post: repo + notebook links for all participants — draft text in checklist
- [ ] Writeup Project Links → this repo (+ notebook / PDF)
- [ ] Optional: export PDF via Public Project Link
- [x] Self-score rubric draft: [`self-score.md`](self-score.md) (revisit after notebook is public)
- [x] Merged cloud polish branch into `main` (`ca16129`)

### Thu Nov 12

- [x] Clarity pass on Abstract + Conclusion (`paper/WRITEUP.md`, mirrored to `DRAFT.md`); paste-map blurb in [`kaggle-publish-checklist.md`](kaggle-publish-checklist.md)
- [ ] Click **Submit** on the Writeup (drafts do not count)
- [ ] Confirm notebook / repo links are public without login

## What must stay out of the paper

- Competition logistics, prize dollar amounts, and day-by-day checklists (keep here)
- Unrun experiment numbers — use TBD until measured, then replace
- Implementation dump — link repo/notebook; keep method prose algorithm-level
