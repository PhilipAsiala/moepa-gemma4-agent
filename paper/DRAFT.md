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

Autonomous software engineering agents powered by small open-weights models (such as the Gemma 4 family) face two fundamental failure modes when operating offline on consumer hardware: (1) **structural hallucination**, where probabilistic token generation violates repository-wide call signatures or import graphs, and (2) **unbounded epistemic loops**, where iterative test-fix cycles exhaust wall-clock and memory budgets on intractable edge cases. We introduce **MOEPA** (Metrology, Ontology, Epistemology, Praxeology, Axiology), a five-layer cognitive governance architecture that wraps small language models in deterministic formal interlocks. By grounding the Ontology layer in the repository’s directed Abstract Syntax Tree (AST) multigraph and dense semantic embeddings, and enforcing Epistemological fail-to-pass verification and Axiological regression-free invariants, MOEPA transforms an unconstrained generative model into a bounded, verifiable state machine. A Metrology layer further enforces dynamic per-task compute telemetry and stagnation detection across a fixed evaluation horizon, preventing localized deadlocks and allocating budget across many tasks. On the 129-task public development set, a lexical seed plus one call-graph hop covers a gold hunk symbol in 19.2% of cases against 3.2% for a size-matched random neighborhood. A 12-task Gemma 4 12B probe names the edited file on 4/12 tasks with that neighborhood and on 3/12 from the issue text alone.

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
4. Measurements on all 129 public tasks for neighborhood coverage and policy gates, plus a 12-task Gemma 4 12B localization probe. End-to-end resolve rate is deferred until repository snapshots are in the loop.

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

Repository snapshots were not checked out, so this section does not report a pytest resolve rate. The numbers below are from `scripts/paper_microbench.py` on the public development assets. Raw rows are in the companion `docs/microbench-results.md`.

### 3.1 Environment

- **Tasks:** 129 public development tasks (67 FastAPI, 48 Rich, 13 Requests, 1 HTTPX) over 127 base commits. Each commit has a paired `graphs/*.json` and `embeddings/*.npz`.
- **Graphs:** directed `calls` edges. Node ids are dotted symbols. Node text is a source snippet.
- **Model:** `gemma4:12b` (about 8 GB) on a local Ollama server, Vulkan, context 4096, thinking disabled for the localization probe. The probe asks for a JSON list of files.
- **What is not in this run:** base-commit checkouts, the official sandbox, and fail-to-pass `pytest`. Those are required for resolve rate and are left out on purpose.

### 3.2 What was measured

1. **Embedding geometry.** Cosine between L2-normalized node vectors on all 127 snapshots (about 200 random pairs each).
2. **Ontology coverage.** Lexical seeds from the issue text, expanded one hop along `calls`. A gold file is covered when a neighborhood id lies in that file's module. A gold hunk symbol is covered when some id ends with that function or class name. The baseline draws the same number of random seeds and expands them the same way (5 trials).
3. **Gates.** Axiology on every gold solution diff, then on that diff with a test file or `imp.py` appended, and on an empty diff. Metrology on repeated versus varied diagnostic signatures.
4. **Gemma localization.** Twelve tasks (1 HTTPX, 3 Requests, 4 Rich, 4 FastAPI), fixed before the run. Two prompts: the issue alone, and the issue plus a 5,000-character cap of the neighborhood. A hit is the same file as the gold diff, ignoring a leading `src/`.

### 3.3 Results

The shipped embeddings are weakly discriminative. Mean cosine is 0.829 for random pairs and 0.829 for cross-parent pairs. Same-parent pairs rise only to 0.885. We did not embed the issue into this space. The competition query encoder is not in this repository, and a vector from another model would not be comparable. Seeding stayed lexical.

The call neighborhood beats chance. It covers 53/278 gold files (19.1%) against a random-neighborhood recall of 0.126, and at least one gold file in 47/129 tasks (36.4%) against 16.4% for the random draws. Hunk-symbol coverage is 70/364 (19.2%) against 3.2%. Thirty-two tasks yield no lexical seed, so the neighborhood is empty. Median neighborhood text is about 10,000 characters and the 90th percentile is about 410,000, so 74/129 neighborhoods do not fit the 4,096-token prompt without a hard cap.

Axiology approves all 129 gold solution diffs and rejects all 129 test-tampered diffs, all 129 shim edits, and the empty diff. Metrology leaves the hop radius at 1 when diagnostics change. On a repeated diagnostic it steps the radius through 1, 2, 3 and stops after four cycles.

Gemma 4 12B does not turn that coverage into better file names on this probe. Issue text alone hits 3/12 files (mean 1.7 s). The capped neighborhood hits 4/12 (mean 3.3 s). Every reply parsed. None abstained. Two of the twelve tasks had an empty neighborhood, so the second prompt could not add code. On several misses the model names a plausible file in another project (`textual`, `typer`, `pytorch`) until the neighborhood pulls the guess back into the target repository, without landing on the edited file.

| Probe | Result |
|---|---|
| Hunk-symbol coverage, lexical + 1 hop | 70/364 (19.2%), random 3.2% |
| Task with ≥1 gold file covered | 47/129 (36.4%), random 16.4% |
| Axiology on gold / tamper / shim / empty | 129 approved / 129 / 129 / 129 rejected |
| Gemma 4 12B file hit, issue only | 3/12, 1.7 s |
| Gemma 4 12B file hit, plus neighborhood | 4/12, 3.3 s |

---

## 4. Related Work

**Repository-level agents and benchmarks.** SWE-bench (Jimenez et al., 2024) established realistic GitHub-issue resolution as an evaluation paradigm. Agentless (Xia et al., 2024) argues for simpler localize-then-edit pipelines over heavy tool loops. MOEPA is complementary: it retains an iterative repair loop but wraps it in explicit governance so small models cannot freely expand scope or spend unbounded compute.

**Graph- and structure-aware code understanding.** Code graphs, ASTs, and embeddings are widely used for retrieval and navigation. MOEPA treats competition-provided AST multigraphs and dense embeddings as a first-class **ontological world model**, not only as retrieval features—boundary enforcement rejects out-of-graph symbols prior to execution.

**Cognitive / neuro-symbolic control.** Classical cognitive architectures separate perception, memory, and motor control (Newell; Laird). Risk-management frameworks for AI systems emphasize measurable controls and stop conditions (e.g., NIST AI RMF). MOEPA imports that separation into offline SWE agents: measurement (Metrology), world model (Ontology), belief update via tests (Epistemology), action (Praxeology), and normative constraints (Axiology).

---

## 5. Discussion and Limitations

**Generality.** Although motivated by an offline sandbox with precomputed graphs and embeddings, the layer split applies to any setting where (i) a structural index of the repo exists or can be built, and (ii) tests provide a cheap epistemic oracle. Without graphs, Ontology degrades to heuristic retrieval; without tests, Epistemology collapses to static checks only.

**Limitations.** These measurements do not include a pytest resolve rate. Thirty-two of 129 issues produce no lexical seed, and most neighborhoods must be truncated before they fit a 4,096-token context, so the Gemma probe often never sees the covered symbol. The 12-task file-hit gap (4/12 versus 3/12) is too small to treat as an effect. Static arity checks are not yet wired into the agent loop. Embedding retrieval cannot be claimed until a query vector is produced in this same 256-d space. Philosophical layer names aid clarity but must not obscure that each layer is a concrete software module with deterministic predicates.

**Ethics / safety.** Axiology’s test-integrity and shim rules reduce a common failure mode (cheating the oracle). Offline deployment reduces dependency on proprietary APIs but still requires care around executing untrusted patches in sandboxes.

---

## 6. Conclusion

MOEPA reframes small-model coding agents as **governed state machines**: graph-grounded context, test-backed truth, policy-backed emission, and metrological budget control. The public call graph does localize gold hunk symbols well above chance, and the policy gate separates solution diffs from test tampering. On a 12-task probe, Gemma 4 12B does not yet convert that neighborhood into more correct file names. We release this writeup (and companion code) to support reproducible research on offline, consumer-hardware agentic software engineering.

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
