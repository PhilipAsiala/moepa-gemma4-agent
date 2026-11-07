# Deterministic Cognitive Governance for Offline Software Engineering Agents: The MOEPA 5-Layer Architecture on Directed AST Multigraphs

**Subtitle:** Bounding Probabilistic Hallucination and Compute Exhaustion in Consumer-Hardware Coding Agents via Metrological, Ontological, Epistemological, Praxeological, and Axiological Interlocks

<!-- WORD BUDGET (≤3000 total; target ~2750) — update counts before submit
  Abstract ............ ~170
  1 Introduction ...... ~420
  2 Methodology ....... ~1100
  3 Experiments ....... ~450  [NEEDS RESULTS]
  4 Related Work ...... ~350
  5 Discussion ........ ~200
  6 Conclusion ........ ~80
  TOTAL TARGET ........ ~2770
-->

<!-- RUBRIC CHECKLIST (score yourself 0–5 before submit)
  Novelty:       five-layer governance + AST-graph ontology + calibrated abstention
  Quality:       ablation design; claim generality beyond SWE-bench sandbox
  Relevance:     offline / consumer-hardware coding agents
  Verifiability: algorithms, gates, metrics, and reproducible ablation table
  Clarity:       short sentences; one figure; consistent layer naming
-->

## Abstract

Small open-weights coding agents (such as Gemma 4) fail offline on consumer hardware in two ways: they invent edits that break call structure or imports (**structural hallucination**), and they burn the whole wall-clock budget retrying one hard bug (**unbounded repair loops**). We introduce **MOEPA** (Metrology, Ontology, Epistemology, Praxeology, Axiology)—five deterministic layers around the language model. Ontology bounds prompt context with the repository’s directed AST multigraph and dense embeddings; Epistemology checks patches with syntax gates and fail-to-pass tests; Axiology blocks test-tampering and unsafe diffs; Metrology tracks per-task time and expands graph hops when progress stalls. The result is a bounded, verifiable control loop rather than an open chat session. On the 129-task public development set, a lexical seed plus one call-graph hop covers a gold hunk symbol in 19.2% of cases against 3.2% for a size-matched random neighborhood. A 30-task Gemma 4 12B probe names the edited file on 14/30 tasks with that neighborhood versus 10/30 from the issue text alone.

**Keywords:** agentic software engineering · offline coding agents · AST multigraphs · graph reasoning · cognitive architectures · Gemma 4

---

## 1. Introduction

Deploying autonomous developer agents in air-gapped or consumer-grade environments requires shifting intelligence from raw parameter scale to **architectural governance**. Frontier models can lean on large context windows and expensive sampling; small open models need structural scaffolding to navigate complex repositories without regressions.

In unconstrained ReAct-style loops, the language model simultaneously acts as navigator, hypothesis generator, verifier, and policy gate. When a small model misreads a traceback, it often enters a degenerative repair loop—editing unrelated files, breaking compatibility shims, or exhausting runtime quotas.

We formalize the **MOEPA Cognitive Architecture**, separating probabilistic synthesis from deterministic verification across five planes:

| Layer | Role | Deterministic artifact |
|-------|------|------------------------|
| **Metrology** | Measurement & telemetry | Per-task time budget $\tau_i$, stagnation metric $M(k)$, hop radius |
| **Ontology** | Structural grounding | Bounded subgraph $G_{\mathrm{sub}}$ from AST multigraph + embeddings |
| **Epistemology** | Truth & verification | Syntax / symbol gates + fail-to-pass `pytest` outcome |
| **Praxeology** | Bounded action | Context-scoped patch $\Delta_k$ from Gemma 4 |
| **Axiology** | Value & policy | Test-integrity, shim preservation, minimal diff, `NO_PATCH` |

**Contributions.**

1. A five-layer governance architecture that makes small offline coding agents behave as bounded state machines rather than open chat loops.
2. An Ontology substrate that uses directed AST multigraphs and dense code embeddings to constrain prompt context and reject out-of-neighborhood symbol use.
3. Deterministic Epistemology and Axiology gates (static AST checks, sandbox tests, policy invariants, calibrated abstention).
4. Measurements on all 129 public tasks for neighborhood coverage and policy gates, a 30-task Gemma 4 12B file-localization probe, snapshot gold-apply / syntax / Axiology on 91 single-file tarballs, and a local wheel-backed pytest gold resolve of 16/20 (fail-baseline 20/20).

---

## 2. Methodology: The MOEPA Pipeline

Each task $T_i$ is processed as a deterministic control loop (Figure 1), not as an open-ended chat session.

```text
                    ┌─────────────────────────────────────┐
                    │           Metrology (L1)            │
                    │  τ_i · cycles · stagnation → hop++  │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │           Ontology (L2)             │
                    │  embeddings → seeds → k-hop G_sub   │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │         Praxeology (L4)             │
                    │     Gemma 4 synthesizes Δ_k         │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │        Epistemology (L3)            │
                    │  AST parse · symbol check · pytest  │
                    └──────────────┬──────────────────────┘
                                   │ pass
                    ┌──────────────▼──────────────────────┐
                    │          Axiology (L5)              │
                    │  policy gates → patch | NO_PATCH    │
                    └─────────────────────────────────────┘
```

*Figure 1. MOEPA control flow. Probabilistic synthesis (L4) is nested inside deterministic measurement, grounding, verification, and policy.*

### 2.1 Layer 1 — Metrology (Compute & Entropy Governance)

Under a hard global wall-clock budget across many tasks, unconstrained retries on one bug starve the remainder. Metrology initializes $\tau_i$ and tracks iterations $k \in \{1,\ldots,K_{\max}\}$. We define a **diagnostic convergence metric**:

$$
M(k) = w_1 \cdot \mathbf{1}[\mathrm{TracebackType}(k)=\mathrm{TracebackType}(k-1)]
      + w_2 \cdot \mathrm{EditDistance}(\Delta_k, \Delta_{k-1})
$$

<!-- Note: draft plan used Δ_TracebackType; the indicator form above is clearer for implementers. -->

If stagnation is detected across consecutive cycles (identical traceback class and near-identical diffs), Metrology triggers an **epistemic pivot**: expand Ontology hop radius by $+1$ instead of resampling the LLM with the same context. Budget exhaustion forces Axiology’s calibrated abstention (`NO_PATCH`).

### 2.2 Layer 2 — Ontology (AST Multigraph & Semantic Grounding)

Small models degrade when flooded with irrelevant files. Ontology builds a bounded subgraph $G_{\mathrm{sub}}=(V_{\mathrm{sub}},E_{\mathrm{sub}})$ from the competition **data substrate**: per-snapshot directed AST multigraphs (`graphs/*.json`) and aligned 256-d dense embeddings (`embeddings/*.npz`, one vector per node id). In the public archives the edges we loaded are `calls` edges between dotted symbol ids, and node text is a source snippet rather than a whole file. Sandbox tools `search_similar_code`, `get_code_neighbors`, and `get_code_subgraph` project the same assets (datasheet: companion repo `docs/data-substrate.md`).

1. **Semantic seed extraction.** Embed the issue text (and optional stack trace) and retrieve top-$N$ seed symbols $V_{\mathrm{seed}}$ via dense code search over the 256-d archive (`search_similar_code`); lexical name match is the offline fallback when no query vector is available.
2. **Directed multigraph expansion.** Traverse caller/callee and inheritance edges from $V_{\mathrm{seed}}$ up to hop depth $h$ (default $h\le 2$, raised by Metrology under stagnation).
3. **Boundary enforcement.** Only symbols in $V_{\mathrm{sub}}$ (plus standard library) enter the prompt. Candidate patches that introduce undefined symbols are rejected *before* test execution.

### 2.3 Layers 4 & 3 — Praxeology subordinated to Epistemology

Praxeology (Gemma 4 patch synthesis) proposes $\Delta_k$ scoped to $G_{\mathrm{sub}}$. Epistemology decides whether the hypothesis is acceptable:

- **Phase A — Localization.** Prefer a deterministic fail-to-pass reproducer from the existing test suite before broad edits.
- **Phase B — Static gate.** `ast.parse` the modified files; check arity / interface compatibility against multigraph neighbors.
- **Phase C — Dynamic gate.** Apply the patch in an offline sandbox and classify `pytest` outcomes into discrete states: `SYNTAX_FAULT`, `IMPORT_FAULT`, `ASSERTION_MISMATCH`, `EPISTEMIC_PASS` (or timeout). Failures feed diagnostics back to Metrology/Ontology.

### 2.4 Layer 5 — Axiology (Policy Interlocks)

A locally green unit test is not sufficient. Before emitting a unified diff, Axiology enforces:

1. **Test integrity** — no deletion, skip marks, or weakened assertions in tests.
2. **Environment / shim preservation** — block edits to sandbox or compatibility infrastructure unless the issue targets them.
3. **Minimal diff (Occam gate)** — strip formatting-only drift; prefer edits inside the fault neighborhood.
4. **Calibrated abstention** — if $\tau_i$ expires without Epistemology + Axiology approval, restore `HEAD` and emit `NO_PATCH`.

---

## 3. Experimental Setup

Numbers below are from `scripts/paper_microbench.py`, `scripts/snapshot_probe.py`, and a local wheel-backed fail-to-pass probe (`scripts/pytest_resolve_probe.py`) on the public development assets. Raw rows are in `docs/microbench-results.md` and `outputs/pytest_resolve.json`.

### 3.1 Environment

- **Tasks:** 129 public development tasks (67 FastAPI, 48 Rich, 13 Requests, 1 HTTPX) over 127 base commits. Each commit has a paired `graphs/*.json` and `embeddings/*.npz`.
- **Graphs:** directed `calls` edges. Node ids are dotted symbols. Node text is a source snippet.
- **Model:** `gemma4:12b` (about 8 GB) on a local Ollama server (Intel Arc Pro B70 via Vulkan), context 4096, thinking disabled for the localization probe. The probe asks for a JSON list of files. Praxeology is wired through the same Ollama client (`src/moepa/llm_ollama.py`) and returns a single-file JSON edit into the agent loop.
- **Snapshots:** public `snapshots/<instance_id>.tgz` archives (git trees at `base_commit`). Gold unified diffs apply after restoring a trailing newline dropped by JSONL.
- **Resolve probe:** competition `wheels/` plus a few pure-Python supplements, executed inside `python:3.13-slim` (host Python is 3.14; many wheels are cp313-only). Targeted tests are those added by each task’s `test_patch`. This is a local Epistemology Phase-C proxy, not the official swegemma two-container verifier.

### 3.2 What was measured

1. **Embedding geometry.** Cosine between L2-normalized node vectors on all 127 snapshots (about 200 random pairs each).
2. **Ontology coverage.** Lexical seeds from the issue text, expanded one hop along `calls`. A gold file is covered when a neighborhood id lies in that file's module. A gold hunk symbol is covered when some id ends with that function or class name. The baseline draws the same number of random seeds and expands them the same way (5 trials).
3. **Gates.** Axiology on every gold solution diff, then on that diff with a test file or `imp.py` appended, and on an empty diff. Metrology on repeated versus varied diagnostic signatures.
4. **Gemma localization.** Expanded 30-task probe for 12B; a separate 12-task comparison for 26B. Two prompts: the issue alone, and the issue plus a 5,000-character cap of the neighborhood. A hit is the same file as the gold diff, ignoring a leading `src/`.
5. **Fail-to-pass resolve.** Stratified 20-task gold probe (Rich / FastAPI / Requests) and a 3-task Praxeology attempt with the pytest gate enabled.

### 3.3 Results

The shipped embeddings are weakly discriminative. Mean cosine is 0.829 for random pairs and 0.829 for cross-parent pairs. Same-parent pairs rise only to 0.885. We did not embed the issue into this space. The competition query encoder is not in this repository, and a vector from another model would not be comparable. Seeding stayed lexical.

The call neighborhood beats chance. It covers 53/278 gold files (19.1%) against a random-neighborhood recall of 0.126, and at least one gold file in 47/129 tasks (36.4%) against 16.4% for the random draws. Hunk-symbol coverage is 70/364 (19.2%) against 3.2%. Thirty-two tasks yield no lexical seed, so the neighborhood is empty. Median neighborhood text is about 10,000 characters and the 90th percentile is about 410,000, so 74/129 neighborhoods do not fit the 4,096-token prompt without a hard cap.

Axiology approves all 129 gold solution diffs and rejects all 129 test-tampered diffs, all 129 shim edits, and the empty diff. Metrology leaves the hop radius at 1 when diagnostics change. On a repeated diagnostic it steps the radius through 1, 2, 3 and stops after four cycles.

On an expanded 30-task Gemma 4 12B probe (fixed quotas across HTTPX / Requests / Rich / FastAPI), issue text alone hits 10/30 files (mean 11.0 s) while the capped neighborhood hits 14/30 (mean 10.7 s). All replies parsed; one abstention on the issue-only arm. The neighborhood often pulls wild cross-project guesses (`textual`, `typer`, `pytorch`) back into the target repository, and lifts file hit rate by four tasks on this sample. The earlier 12-task pilot (3/12 → 4/12) was too small to treat as an effect; the 30-task sample is still modest but directionally consistent.

On all 91 single-file gold tasks among the 129 public snapshots, every gold solution diff applies cleanly and every touched `.py` file still parses; Axiology approves 90/91 resulting diffs (`scripts/snapshot_probe.py`; the miss edits a protected shim path).

On a stratified 20-task wheel-backed pytest probe, every task fails its targeted tests before the gold patch (`20/20`) and gold resolves `16/20` after apply (all 7 Rich and 6 Requests in the sample; 3/7 FastAPI—four FastAPI trees need packages beyond the local shelf). A 12-task Gemma 4 26B localization comparison is weaker than 12B on the same small slice (issue-only 1/12, neighborhood 3/12), with heavy abstention. Enabling the pytest gate in the Praxeology loop yields `0/3` patches on tasks where gold already resolves; the earlier syntax-only smoke was `1/3` Axiology-approved edits.

| Probe | Result |
|---|---|
| Hunk-symbol coverage, lexical + 1 hop | 70/364 (19.2%), random 3.2% |
| Task with ≥1 gold file covered | 47/129 (36.4%), random 16.4% |
| Axiology on gold / tamper / shim / empty | 129 approved / 129 / 129 / 129 rejected |
| Gemma 4 12B file hit, issue only (n=30) | 10/30, 11.0 s |
| Gemma 4 12B file hit, plus neighborhood (n=30) | 14/30, 10.7 s |
| Gemma 4 26B file hit, issue / neighborhood (n=12) | 1/12 / 3/12 |
| Snapshot gold apply / syntax / Axiology (n=91) | 91 / 91 / 90 |
| Local wheel pytest gold resolve (n=20) | 16/20 (fail-baseline 20/20) |
| Praxeology + pytest gate (n=3) | 0/3 patches |

---

## 4. Related Work

**Repository-level agents and benchmarks.** SWE-bench (Jimenez et al., 2024) established realistic GitHub-issue resolution as an evaluation paradigm. Agentless (Xia et al., 2024) argues for simpler localize-then-edit pipelines over heavy tool loops. MOEPA is complementary: it retains an iterative repair loop but wraps it in explicit governance so small models cannot freely expand scope or spend unbounded compute.

**Graph- and structure-aware code understanding.** Code graphs, ASTs, and embeddings are widely used for retrieval and navigation. MOEPA treats competition-provided AST multigraphs and dense embeddings as a first-class **ontological world model**, not only as retrieval features—boundary enforcement rejects out-of-graph symbols prior to execution.

**Cognitive / neuro-symbolic control.** Classical cognitive architectures separate perception, memory, and motor control (Newell; Laird). Risk-management frameworks for AI systems emphasize measurable controls and stop conditions (e.g., NIST AI RMF). MOEPA imports that separation into offline SWE agents: measurement (Metrology), world model (Ontology), belief update via tests (Epistemology), action (Praxeology), and normative constraints (Axiology).

---

## 5. Discussion and Limitations

**Generality.** Although motivated by an offline sandbox with precomputed graphs and embeddings, the layer split applies to any setting where (i) a structural index of the repo exists or can be built, and (ii) tests provide a cheap epistemic oracle. Without graphs, Ontology degrades to heuristic retrieval; without tests, Epistemology collapses to static checks only.

**Limitations.** The local resolve probe is not the official swegemma verifier; four FastAPI tasks in the 20-task sample still miss deps, and agent pytest resolve remains 0/3. Thirty-two of 129 issues produce no lexical seed, and most neighborhoods must be truncated before they fit a 4,096-token context, so the Gemma probe often never sees the covered symbol. The 30-task file-hit lift (14/30 versus 10/30) is suggestive, not definitive. Static arity checks exist in the method but are only lightly used in the agent loop. Embedding retrieval cannot be claimed until a query vector is produced in this same 256-d space. Philosophical layer names aid clarity but must not obscure that each layer is a concrete software module with deterministic predicates.

**Ethics / safety.** Axiology’s test-integrity and shim rules reduce a common failure mode (cheating the oracle). Offline deployment reduces dependency on proprietary APIs but still requires care around executing untrusted patches in sandboxes.

---

## 6. Conclusion

MOEPA treats small-model coding agents as **governed state machines**: graph-bounded context, test-backed checks, policy gates on emitted diffs, and per-task budget control. The public call graph finds gold hunk symbols well above chance; policy gates accept gold solution diffs and reject test tampering on real snapshots; and a 30-task Gemma 4 12B probe shows a modest file-hit lift with the capped neighborhood (14/30 vs 10/30). A local wheel-backed pytest probe resolves 16/20 gold patches, while the pytest-gated Praxeology loop still abstains (0/3)—the intended high bar. We release this writeup and companion code for reproducible work on offline, consumer-hardware agentic software engineering.

---

## References

1. Jimenez, C. E., et al. (2024). *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?* ICLR. https://arxiv.org/abs/2310.06770
2. Xia, C. S., et al. (2024). *Agentless: Demystifying LLM-based Software Engineering Agents.* https://arxiv.org/abs/2407.01489
3. Laird, J. E. (2012). *The Soar Cognitive Architecture.* MIT Press.
4. Newell, A. (1990). *Unified Theories of Cognition.* Harvard University Press.
5. NIST (2023). *Artificial Intelligence Risk Management Framework (AI RMF 1.0).*
6. Markowitz, E., et al. (2026). *Google – The Gemma 4 Developer Agent Paper Track.* Kaggle. https://www.kaggle.com/competitions/gemma-4-developer-agent-paper

<!-- Optional citation expansions once notebook / model card exist:
   - Yao et al. ReAct
   - additional graph-code / RAG-for-code papers you actually cite in prose
-->
