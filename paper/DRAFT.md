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

Autonomous software engineering agents powered by small open-weights models (such as the Gemma 4 family) face two fundamental failure modes when operating offline on consumer hardware: (1) **structural hallucination**, where probabilistic token generation violates repository-wide call signatures or import graphs, and (2) **unbounded epistemic loops**, where iterative test-fix cycles exhaust wall-clock and memory budgets on intractable edge cases. We introduce **MOEPA** (Metrology, Ontology, Epistemology, Praxeology, Axiology), a five-layer cognitive governance architecture that wraps small language models in deterministic formal interlocks. By grounding the Ontology layer in the repository’s directed Abstract Syntax Tree (AST) multigraph and dense semantic embeddings, and enforcing Epistemological fail-to-pass verification and Axiological regression-free invariants, MOEPA transforms an unconstrained generative model into a bounded, verifiable state machine. A Metrology layer further enforces dynamic per-task compute telemetry and stagnation detection across a fixed evaluation horizon, preventing localized deadlocks and allocating budget across many tasks. <!-- [TODO: one sentence with headline ablation result once measured] -->

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
4. An ablation protocol on repository-level Python tasks that isolates the incremental value of each governance layer. <!-- [TODO: replace with measured contribution once experiments land] -->

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

Small models degrade when flooded with irrelevant files. Ontology builds a bounded subgraph $G_{\mathrm{sub}}=(V_{\mathrm{sub}},E_{\mathrm{sub}})$:

1. **Semantic seed extraction.** Embed the issue text (and optional stack trace) and retrieve top-$N$ seed symbols $V_{\mathrm{seed}}$ via dense code search (256-d embeddings).
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

<!-- STATUS: design locked; numbers are PLACEHOLDERS until the micro-benchmark runs. -->

### 3.1 Environment

- **Tasks:** public development split of repository-level Python bug-fix tasks (offline sandbox).
- **Model:** Gemma 4 (open weights), local / offline inference. <!-- [TODO: exact variant + quantization] -->
- **Assets:** directed AST multigraphs + 256-d dense embeddings for retrieval and subgraph expansion.
- **Metrics:** resolve rate (fail-to-pass without pass-to-pass regressions), mean wall time / task, regression / corrupted-diff rate, abstention rate (`NO_PATCH`).

### 3.2 Ablation protocol

We ablate governance layers on a fixed public subset (target: full public split; first pass: 20–30 tasks for speed).

| Configuration | L2 Ontology | L3 Epistemology | L1 Metrology | L5 Axiology | Resolve % | Avg s/task | Regressions |
|---------------|:-----------:|:---------------:|:------------:|:-----------:|:---------:|:----------:|:-----------:|
| Gemma 4 ReAct baseline | – | – | – | – | TBD | TBD | TBD |
| + Ontology | ✓ | – | – | – | TBD | TBD | TBD |
| + Ontology + Epistemology | ✓ | ✓ | – | – | TBD | TBD | TBD |
| Full MOEPA | ✓ | ✓ | ✓ | ✓ | TBD | TBD | TBD |

**Hypotheses.** Ontology should cut irrelevant context and structural hallucination; Epistemology should cut syntax/import failures reaching submission; Metrology should improve multi-task throughput under a fixed wall; Axiology should drive regressions toward zero at some cost in abstention.

### 3.3 Results

<!-- [TODO] Fill after Saturday–Monday micro-benchmark. Lead with 2–3 sentences + the completed table. Optional: failure-mode breakdown (hallucinated imports vs loop exhaustion vs policy reject). -->

---

## 4. Related Work

**Repository-level agents and benchmarks.** SWE-bench (Jimenez et al., 2024) established realistic GitHub-issue resolution as an evaluation paradigm. Agentless (Xia et al., 2024) argues for simpler localize-then-edit pipelines over heavy tool loops. MOEPA is complementary: it retains an iterative repair loop but wraps it in explicit governance so small models cannot freely expand scope or spend unbounded compute.

**Graph- and structure-aware code understanding.** Code graphs, ASTs, and embeddings are widely used for retrieval and navigation. MOEPA treats competition-provided AST multigraphs and dense embeddings as a first-class **ontological world model**, not only as retrieval features—boundary enforcement rejects out-of-graph symbols prior to execution.

**Cognitive / neuro-symbolic control.** Classical cognitive architectures separate perception, memory, and motor control (Newell; Laird). Risk-management frameworks for AI systems emphasize measurable controls and stop conditions (e.g., NIST AI RMF). MOEPA imports that separation into offline SWE agents: measurement (Metrology), world model (Ontology), belief update via tests (Epistemology), action (Praxeology), and normative constraints (Axiology).

---

## 5. Discussion and Limitations

**Generality.** Although motivated by an offline sandbox with precomputed graphs and embeddings, the layer split applies to any setting where (i) a structural index of the repo exists or can be built, and (ii) tests provide a cheap epistemic oracle. Without graphs, Ontology degrades to heuristic retrieval; without tests, Epistemology collapses to static checks only.

**Limitations.** <!-- refine after results --> Calibrated abstention trades resolve rate for safety. Static arity checks do not capture semantic contracts. Embedding retrieval can miss the true fault locus. Philosophical layer names aid clarity but must not obscure that each layer is a concrete software module with deterministic predicates.

**Ethics / safety.** Axiology’s test-integrity and shim rules reduce a common failure mode (cheating the oracle). Offline deployment reduces dependency on proprietary APIs but still requires care around executing untrusted patches in sandboxes.

---

## 6. Conclusion

MOEPA reframes small-model coding agents as **governed state machines**: graph-grounded context, test-backed truth, policy-backed emission, and metrological budget control. <!-- [TODO: one sentence summarizing the strongest ablation finding.] --> We release this writeup (and companion code) to support reproducible research on offline, consumer-hardware agentic software engineering.

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
