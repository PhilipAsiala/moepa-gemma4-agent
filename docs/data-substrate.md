# Data substrate (competition assets → MOEPA layers)

This repository’s Ontology layer is not a free-form RAG box. It is a **bounded world model** over assets the competition ships and tools the sandbox exposes. The paper calls that world model the Ontology substrate; this page is the datasheet: what arrives on disk, what each MOEPA layer reads, and which code path consumes it.

Canonical code: [`src/moepa/ontology.py`](../src/moepa/ontology.py) (`OntologySubstrate`), orchestrated by [`src/moepa/agent.py`](../src/moepa/agent.py). Method prose: [`paper/DRAFT.md`](../paper/DRAFT.md) §2.2.

## What the competition provides

Public development set (Paper Track / Main Track shared assets). Exact paths follow the competition Data tab; locally we expect something equivalent to:

| Asset | Typical path | Role in MOEPA |
| --- | --- | --- |
| Task list | `tasks.jsonl` | One JSON object per issue: id, repo, problem statement, base commit, FAIL_TO_PASS / PASS_TO_PASS test names. Metrology keys the loop on `task["id"]`. |
| Directed AST multigraphs | `graphs/*.json` | Per-snapshot typed multigraph. Ontology’s structural index: nodes = symbols (file / class / function), edges = structural relations. |
| Dense code embeddings | `embeddings/*.npz` | Per-node 256-d `float32` vectors (one array per node id). Dense retrieval seed for Ontology (`search_similar_code` in the sandbox). |
| Offline sandbox | Python 3.13 `swebench-sandbox` | Epistemology’s dynamic gate (`pytest`) and Praxeology’s apply/reset surface. |
| Eval budget | `eval_config.yaml` (Main Track) | Metrology’s wall-clock and per-task budget source of truth under the 12-hour horizon. |

Public split size named in the plan: **129** development tasks across repositories such as FastAPI, Rich, Requests, and HTTPX, with a held-out test split of similar scale. Numbers on the Data tab win if they disagree with this page.

Submissions that reason over the graph and embedding dataset are explicitly encouraged by the competition (Graph Reasoning / Code Comprehension topics). That is why Ontology is a first-class layer here rather than a retrieval helper.

## Graph schema (as consumed by this repo)

`OntologySubstrate` loads a graph JSON with at least:

```json
{
  "nodes": [
    { "id": "path/to/mod.py:Class.method", "text": "<source span>" }
  ],
  "edges": [
    { "source": "<node id>", "target": "<node id>" }
  ]
}
```

Competition graphs are typed multigraphs in the LocAgent style: node kinds file / class / function; edge kinds typically **CONTAIN**, **IMPORT**, **INVOKE**, **INHERIT**. The current loader is type-agnostic: it expands along every edge, treating the neighborhood as undirected for context gathering (see `get_code_neighbors`). Typed filters can be added without changing the rest of the stack.

Sandbox tools that project the same substrate:

| Tool | Layer use |
| --- | --- |
| `search_similar_code` | Ontology seed extraction over the 256-d embeddings |
| `get_code_neighbors` | Ontology 1-hop expansion (caller / callee / inheritance) |
| `get_code_subgraph` | Ontology *k*-hop bounded subgraph $G_{\mathrm{sub}}$ |

Offline micro-benchmarks can call the same logic through `OntologySubstrate` without the tool RPC, once `graphs/` and `embeddings/` are on disk.

## Embedding schema

- Dimensionality: **256**.
- Storage: NumPy `.npz` under `embeddings/` — keys are graph `node_id`s, values are `float32[256]`. Files are typically named `<repo>_<base_commit>.npz` (CLI download); Kaggle may also expose task-named hardlinks.
- Intended use: dense similarity of the issue text (and optional traceback) against node vectors to produce $V_{\mathrm{seed}}$, then expand structurally.

`OntologySubstrate` stacks `.npz` entries into an `(N, 256)` matrix aligned to graph node order when `embedding_path` is given. Seed ranking by cosine is available once a query vector is supplied (`rank_seeds_by_embedding`). Producing that query vector is the sandbox’s `search_similar_code` (or a local embedder in a notebook). Lexical name match (`seed_symbols_from_text`) remains the offline fallback used by the agent skeleton when no query embedding is available.

Independent Paper Track probes have reported that these embeddings can be weakly discriminative (near-uniform cosines). That is an empirical claim about the asset, not a reason to drop it: Ontology still **bounds** context with the graph even when the seed comes from lexical match. The ablation in §3 is designed to measure what the graph + embedding substrate actually buys under MOEPA gates.

## Layer-for-layer map

| MOEPA layer | Deterministic artifact | Substrate it reads |
| --- | --- | --- |
| **Metrology** | $\tau_i$, stagnation $M(k)$, hop radius | `tasks.jsonl` id; wall budget from eval config; cycle diagnostics from Epistemology |
| **Ontology** | Bounded $G_{\mathrm{sub}}$ | `graphs/*.json` + `embeddings/*.npz` (+ sandbox graph/embedding tools) |
| **Praxeology** | Context-scoped patch $\Delta_k$ | Working tree under the sandbox; prompt context = Ontology map only |
| **Epistemology** | Syntax / symbol / `pytest` outcome | Repo files + FAIL_TO_PASS tests named on the task |
| **Axiology** | Policy approve / `NO_PATCH` | Unified diff + protected shim / test-file rules |

What this competition substrate is **not**:

- It is not the enterprise Iceberg ledger (`DS1`) of the thesis architecture. Here the system of record for a task is the git tree at the base commit plus the issued tests.
- The AST multigraph is the **ontological projection** for one repository snapshot (closest cousin in the catalog: `DS3`). The `.npz` archive is the **epistemic retrieval index** for that snapshot (closest cousin: `DS4`). Both are precomputed projections the agent must treat as authoritative for the run, the same way the enterprise stack rebuilds projections from the ledger.
- Decision history in this agent is the Metrology cycle log plus the final patch or `NO_PATCH` (a thin stand-in for `DS5`); it is not yet an append-only ledger row.

## How the agent uses it (code path)

1. `MOEPAGemmaAgent.solve_task` builds `MetrologyState(task_id=…)`.
2. Seeds: `_extract_initial_symbols` → lexical fallback today; prefer `OntologySubstrate.rank_seeds_by_embedding` when a query vector exists.
3. Each cycle: `ontology.build_bounded_context(seeds, hops=metrology.ast_hop_radius)` → `{symbol_id: source_text}` injected into Praxeology.
4. On stagnation (identical diagnostic signature), Metrology raises `ast_hop_radius` by +1 (capped) instead of resampling the same neighborhood.
5. Epistemology runs `ast.parse` then `pytest`; failures feed Metrology. Axiology inspects the diff before emission.

## Local layout for experiments

```text
data/
  tasks.jsonl
  graphs/          # *.json snapshots
  embeddings/      # *.npz aligned to those snapshots
  repos/           # optional clones for offline apply/test
```

Download from the competition Data tab (requires a Kaggle account). Do not commit the assets; they are large and redistributed by Kaggle. Point `OntologySubstrate(graph_path=…, embedding_path=…)` at the snapshot that matches the task’s graph key.

## Claims this page supports

- Verifiability: readers can see which files and tools the method depends on.
- Relevance / Best New Application: MOEPA as governance **of** the provided graph + embedding substrate, not instead of it.
- Best New Resource: a public notebook that walks `graphs/` + `embeddings/` through `OntologySubstrate` (see [`../notebooks/moepa-graph-walkthrough.md`](../notebooks/moepa-graph-walkthrough.md)).
