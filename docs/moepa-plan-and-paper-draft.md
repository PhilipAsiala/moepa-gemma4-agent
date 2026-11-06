# **MOEPA Architecture: Google – The Gemma 4 Developer Agent Competition Plan & Paper Draft**

# **Executive Overview & Competition Fit**

1. **The Paper Track (\$35,000 Pool) is due November 12, 2026 (11:59 PM UTC), and code submission is OPTIONAL for the Paper Track.** Requires a maximum 3,000-word research writeup (plus an optional public repo or notebook link) and is non-archival—meaning it can still be published in a thesis or academic venue later.  
2. **The Dataset & Tools Match MOEPA Layer-for-Layer:** Google DeepMind provides 129 development tasks (and \~120 hidden test tasks) built on an offline Python 3.13 `swebench-sandbox`. Crucially, they explicitly provide directed AST multigraphs (`get_code_neighbors`, `get_code_subgraph`) and 256-dim dense semantic vector embeddings (`search_similar_code`), and state that submissions leveraging the accompanying graph and embedding dataset for Graph Reasoning are highly encouraged.  
3. **The Main Code Track (\$65,000 \+ \$10K Small Model Bonus) stays open until December 2, 2026** (entry deadline November 25, 2026), providing a 12-hour evaluation window (`eval_config.yaml`) to run the offline agent.

# **Part 1: Paper Track Draft (Due Nov 12, 2026\)**

*Word limit: 3,000 words maximum. Target prize tracks: Overall Best Paper (\$15,000) and Best New Application / Resource (\$10,000).*

# **Title**

**Deterministic Cognitive Governance for Offline Software Engineering Agents: The MOEPA 5-Layer Architecture on Directed AST Multigraphs**

# **Subtitle**

*Bounding Probabilistic Hallucination and Compute Exhaustion in Consumer-Hardware Coding Agents via Metrological, Ontological, Epistemological, Praxeological, and Axiological Interlocks*

# **1\. Abstract**

Autonomous software engineering agents powered by small open-weights models (such as the Gemma 4 family) face two fundamental failure modes when operating offline on consumer hardware: (1) structural hallucination, where probabilistic token generation violates repository-wide call signatures or import graphs, and (2) *unbounded epistemic loops*, where iterative test-fix cycles exhaust strict wall-clock and VRAM budgets on intractable edge cases. We introduce **MOEPA** (Metrology, Ontology, Epistemology, Praxeology, Axiology), a five-layer cognitive governance architecture that wraps small language models in deterministic formal interlocks. By grounding the Ontology layer directly in the repository’s directed Abstract Syntax Tree (AST) multigraph and dense semantic embeddings, and enforcing pre-execution **Epistemological** (fail-to-pass unit test verification) and Axiological (regression-free invariant) gates, MOEPA transforms an unconstrained generative model into a bounded, verifiable state machine. Furthermore, our **Metrology** layer enforces dynamic per-task compute telemetry and entropy budgeting across the 12-hour sandbox horizon, preventing localized deadlocks and maximizing global patch resolution rates.

# **2\. Introduction**

Deploying autonomous developer agents in air-gapped or consumer-grade local environments requires shifting intelligence from raw parameter scale to architectural governance. While frontier models rely on massive context windows and brute-force sampling to resolve repository-level bugs, small open models require strict structural scaffolding to navigate complex codebases without introducing regressions.

In standard ReAct (Reason \+ Act) or unconstrained agentic loops, the language model simultaneously acts as navigator, hypothesis generator, verifier, and policy gate. When a small model misinterprets a traceback, it frequently enters a degenerative repair loop—modifying unrelated files, breaking existing compatibility shims, or exhausting runtime quotas.

To solve this, we formalize the **MOEPA Cognitive Architecture**, separating probabilistic synthesis from deterministic verification across five formal philosophical and systems-engineering planes:

* **Metrology (Measurement & Telemetry):** Quantifies token entropy, AST traversal depth, and wall-clock execution budgets per task.  
* **Ontology (Structural Grounding):** Constrains the agent’s world-model to verified entities within the directed AST symbol multigraph (`nodes`, `edges`) and dense vector substrate (`.npz` embeddings).  
* **Epistemology (Truth & Verification):** Validates whether a candidate hypothesis logically resolves the fault via isolated `pytest` reproduction (`Fail-to-Pass` state transition).  
* **Praxeology (Bounded Action):** Executes context-minimal, syntax-verified code transformations (`git diff` synthesis) using the Gemma 4 backbone.  
* **Axiology (Value & Policy Governance):** Enforces non-negotiable safety and regression invariants (`Pass-to-Pass` preservation, zero test-suite tampering, and minimal diff footprint) prior to emitting the final patch.

# **3\. Methodology: The 5-Layer MOEPA Pipeline**

Every bug-fixing instance \$T\_i\$ in \$T\$ is processed not as an open-ended chat session, but as a deterministic state machine governed by the five MOEPA layers:

* **Layer 1: Metrology (Compute & Entropy Telemetry Gate):** Allocates dynamic time budget \$\\tau\_i\$ (via `eval_config.yaml`) and monitors cycle count, token entropy, and AST hop depth.  
* **Layer 2: Ontology (Directed AST Multigraph & Vector Substrate):** Queries `search_similar_code` (256-d `.npz` dense embeddings), traverses `get_code_neighbors` and `get_code_subgraph`, and constructs a bounded k-hop Symbol Context Graph \$G\_{sub}\$.  
* **Layer 4: Praxeology (Gemma 4 Bounded Action & Patch Synthesis):** Synthesizes candidate patch \$\\Delta\_k\$ strictly scoped to \$G\_{sub}\$.  
* **Layer 3: Epistemology (Deterministic Truth Verification):** Checks AST syntax validity and symbol reference integrity, then executes the sandbox `pytest` harness (Fail-to-Pass verification). If failed and time remains, feeds diagnostics back to Layer 1/2.  
* **Layer 5: Axiology (Policy & Regression Interlock):** Blocks modifications to test assertions or build shims, verifies full Pass-to-Pass regression suite and minimal diff, and emits a verified unified diff patch (or deterministic `NO_PATCH`).

## **3.1 Layer 1: Metrology (Compute & Entropy Governance)**

Given the competition's hard 12-hour global execution wall across \~120 hidden test tasks, unconstrained retries on a single complex bug can starve downstream tasks. The Metrology layer initializes a task budget \$\\tau\_i\$ (e.g., \$\\tau\_{max} \= 300s\$) and tracks state progress across iterations \$k \\in {1 \\dots K\_{max}}\$. We define a **Diagnostic Convergence Metric** \$M(k)\$:

\$\$M(k) \= w\_1 \\cdot \\Delta\_{TracebackType}(k) \+ w\_2 \\cdot EditDistance(\\Delta\_k, \\Delta\_{k-1})\$\$

If \$M(k) \= 0\$ across two consecutive repair cycles (indicating the model is generating semantically identical patches or hitting the exact same stack trace), the Metrology gate triggers an immediate **Epistemic Pivot**—forcing Layer 2 (Ontology) to expand the AST subgraph radius by \+1 hop rather than resampling the LLM with the same context.

## **3.2 Layer 2: Ontology (AST Multigraph & Semantic Grounding)**

Small language models degrade rapidly when flooded with irrelevant repository files. Instead of raw file-tree grepping, MOEPA’s Ontology layer builds a formal, mathematically bounded Subgraph Context \$G\_{sub} \= (V\_{sub}, E\_{sub})\$ using the competition's pre-computed graph and embedding assets:

1. **Semantic Seed Extraction:** The issue description and initial stack trace are embedded and matched against the 256-dimensional `float32` `.npz` archives via `search_similar_code` to identify top-N seed symbol nodes \$V\_{seed}\$.  
2. **Directed Multigraph Expansion:** Using `get_code_neighbors` and `get_code_subgraph`, the Ontology layer traverses incoming caller edges and outgoing callee/inheritance edges from \$V\_{seed}\$ up to hop depth \$h \\le 2\$.  
3. **Ontological Boundary Enforcement:** Only symbol nodes \$v \\in V\_{sub}\$ and their explicit interface signatures are injected into the prompt context. Any candidate patch generated in Layer 4 that invokes a symbol undefined in \$V\_{sub}\$ or standard library scope is rejected *prior* to test execution.

## **3.3 Layer 4 & Layer 3: Praxeology & Epistemology (Action-Verification Duality)**

Within MOEPA, **Praxeology** (Gemma 4 patch synthesis) is strictly subordinate to Epistemology (how the system knows a patch is true).

* **Phase A (Reproducer Synthesis / Fault Localization):** Before editing functional source code, the Epistemology layer verifies whether a deterministic fail-to-pass reproducer exists in the test suite.  
* **Phase B (Static Epistemic Gate):** When Gemma 4 proposes a candidate diff \$\\Delta\_k\$, Layer 3 parses the modified file via Python’s `ast.parse()` and verifies that all modified symbol definitions preserve arity and type-hint compatibility with their parent/child nodes in the AST multigraph.  
* **Phase C (Dynamic Epistemic Gate):** The patch is applied in the Python 3.13 `swebench-sandbox`. The Epistemology layer parses the `pytest` exit code and structured traceback, classifying outcomes into deterministic states: `SYNTAX_FAULT`, `IMPORT_FAULT`, `ASSERTION_MISMATCH`, or `EPISTEMIC_PASS`.

## **3.4 Layer 5: Axiology (Deterministic Policy & Value Interlocks)**

A patch that passes a localized unit test may still violate software engineering invariants. Before committing a `git diff HEAD` to `submission.jsonl`, the Axiology layer enforces four hard deterministic policy gates (implemented as lightweight in-memory Python policy evaluators):

1. **Test Integrity Invariant:** The agent is strictly forbidden from deleting, skipping (`@pytest.mark.skip`), or weakening existing unit test assertions in `test_*.py` to artificially achieve an exit code of 0\.  
2. **Environment Shim Preservation:** Prohibits modifications to sandbox infrastructure or Python 3.13 compatibility shims (`imp.py`, `telnetlib.py`, `pyproject.toml` build backends) unless explicitly targeted by the issue.  
3. **Minimal Diff Parsimony (Occam's Gate):** Computes the ratio of modified AST nodes to fault-neighborhood nodes. Unnecessary formatting drift or collateral refactoring is stripped.  
4. **Calibrated Abstention (`NO_PATCH` Policy):** If \$\\tau\_i\$ expires without satisfying both Layer 3 (Epistemology) and Layer 5 (Axiology), MOEPA deterministically restores `HEAD` and emits `NO_PATCH`, preserving repository integrity and downstream compute budget.

# **4\. Experimental Setup & Ablation Design (For the 129 Public Dev Tasks)**

To demonstrate **Verifiability** and **Quality/Universality**, experiments are structured around an ablation of the MOEPA layers on the 129 public development tasks:

| Agent Configuration | AST Graph \+ .npz Ontology (L2) | Epistemic Loop \+ Static AST Gate (L3) | Metrology Time/Loop Breaker (L1) | Axiology Policy Gate (L5) | Resolved % (Pass-to-Pass) | Avg. Time / Task (sec) | Uncaught Regressions / Corrupted Diffs |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| Baseline: Unconstrained Gemma 4 ReAct | No | No | No | No | \[Run Baseline\] | \[High / Timeouts\] | \[High\] |
| \+ MOEPA Ontology Only | Yes | No | No | No | \[+X%\] | \[Reduced\] | \[Moderate\] |
| \+ MOEPA Ontology & Epistemology | Yes | Yes | No | No | \[+Y%\] | \[Moderate\] | \[Low\] |
| Full 5-Layer MOEPA Architecture | Yes | Yes | Yes | Yes | \[Highest %\] | \[Bounded \< 240s\] | 0.0% |

# **5\. Related Works & Universal Impact**

Cite SWE-bench [(Jimenez et al., 2024\)](https://arxiv.org/abs/2310.06770), Agentless [(Xia et al., 2024\)](https://arxiv.org/abs/2407.01489), and Neuro-Symbolic / Cognitive Architectures (Laird, Newell; NIST AI RMF), highlighting that MOEPA bridges enterprise deterministic governance with resource-constrained local software engineering agents.

# **Part 2: Python Implementation Skeleton (`moepa_gemma_agent.py`)**

```py
"""
MOEPA 5-Layer Cognitive Agent for Google Gemma 4 Developer Agent Competition
Layers: Metrology | Ontology | Epistemology | Praxeology | Axiology
Compatible with offline Python 3.13 swebench-sandbox
"""

import ast
import json
import time
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import numpy as np


# ============================================================================
# LAYER 1: METROLOGY (Telemetry, Compute Budgeting & Loop-Death Prevention)
# ============================================================================
@dataclass
class MetrologyState:
    task_id: str
    max_wall_seconds: float = 270.0  # Ensures 120 tasks finish well under 12h limit
    max_epistemic_cycles: int = 4
    start_time: float = field(default_factory=time.monotonic)
    cycle_count: int = 0
    traceback_signatures: List[str] = field(default_factory=list)
    ast_hop_radius: int = 1

    def remaining_seconds(self) -> float:
        return max(0.0, self.max_wall_seconds - (time.monotonic() - self.start_time))

    def budget_exhausted(self) -> bool:
        return (
            self.remaining_seconds() <= 15.0
            or self.cycle_count >= self.max_epistemic_cycles
        )

    def record_and_check_stagnation(self, tb_signature: str) -> bool:
        """Detects epistemic loop stagnation; triggers Ontology hop expansion if stuck."""
        self.cycle_count += 1
        self.traceback_signatures.append(tb_signature)
        if len(self.traceback_signatures) >= 2:
            if self.traceback_signatures[-1] == self.traceback_signatures[-2]:
                self.ast_hop_radius = min(3, self.ast_hop_radius + 1)
                return True
        return False


# ============================================================================
# LAYER 2: ONTOLOGY (Directed AST Multigraph & 256-d Embedding Substrate)
# ============================================================================
class OntologySubstrate:
    def __init__(self, graph_path: Path, embedding_path: Path):
        with open(graph_path, "r", encoding="utf-8") as f:
            self.graph_data = json.load(f)
        self.nodes: Dict[str, dict] = {
            n["id"]: n for n in self.graph_data.get("nodes", [])
        }
        self.edges: List[dict] = self.graph_data.get("edges", [])
        self.embeddings = np.load(embedding_path) if embedding_path.exists() else None

    def get_code_neighbors(self, symbol_id: str, hops: int = 1) -> Set[str]:
        """Traverses directed AST multigraph edges up to k hops."""
        visited: Set[str] = {symbol_id}
        frontier: Set[str] = {symbol_id}
        for _ in range(hops):
            next_frontier: Set[str] = set()
            for edge in self.edges:
                src, dst = edge.get("source"), edge.get("target")
                if src in frontier and dst in self.nodes and dst not in visited:
                    next_frontier.add(dst)
                elif dst in frontier and src in self.nodes and src not in visited:
                    next_frontier.add(src)
            visited.update(next_frontier)
            frontier = next_frontier
        return visited

    def build_bounded_context(self, seed_symbols: List[str], hops: int = 1) -> Dict[str, str]:
        """Constructs the formal ontological context map {symbol_id: source_text}."""
        active_symbols: Set[str] = set()
        for sym in seed_symbols:
            if sym in self.nodes:
                active_symbols.update(self.get_code_neighbors(sym, hops=hops))
        return {
            sym_id: self.nodes[sym_id].get("text", "")
            for sym_id in active_symbols
            if sym_id in self.nodes
        }


# ============================================================================
# LAYER 3: EPISTEMOLOGY (Static AST Verification & Sandbox Pytest Harness)
# ============================================================================
class EpistemologyVerifier:
    @staticmethod
    def verify_python_syntax(file_path: Path) -> Tuple[bool, str]:
        """Deterministic pre-execution check: ensures modified file parses cleanly."""
        try:
            source = file_path.read_text(encoding="utf-8")
            ast.parse(source, filename=str(file_path))
            return True, "SYNTAX_VALID"
        except SyntaxError as e:
            return False, f"SYNTAX_FAULT: {e.msg} at line {e.lineno}"

    @staticmethod
    def run_verification_tests(repo_dir: Path, timeout_sec: float) -> Tuple[bool, str]:
        """Executes offline pytest suite to verify Fail-to-Pass transition."""
        try:
            proc = subprocess.run(
                ["pytest", "-q", "--tb=short", "--disable-warnings"],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
                timeout=max(10.0, min(90.0, timeout_sec)),
            )
            if proc.returncode == 0:
                return True, "EPISTEMIC_PASS"
            lines = (proc.stdout + "\n" + proc.stderr).strip().splitlines()
            signature = "\n".join(lines[-8:]) if lines else "UNKNOWN_TEST_FAILURE"
            return False, signature
        except subprocess.TimeoutExpired:
            return False, "TIMEOUT_FAULT"


# ============================================================================
# LAYER 5: AXIOLOGY (Deterministic Policy & Regression Interlocks)
# ============================================================================
class AxiologyPolicyGate:
    PROTECTED_SHIMS = {"imp.py", "telnetlib.py", "pyproject.toml", "setup.cfg"}

    @classmethod
    def evaluate_patch_policy(cls, unified_diff: str, allow_config_edits: bool = False) -> Tuple[bool, str]:
        """Hard deterministic policy gate before patch emission."""
        if not unified_diff or not unified_diff.strip():
            return False, "AXIOLOGY_REJECT: Empty patch"

        modified_files = []
        for line in unified_diff.splitlines():
            if line.startswith("+++ b/"):
                modified_files.append(line[6:].strip())

        for mod_file in modified_files:
            fname = Path(mod_file).name
            if not allow_config_edits and fname in cls.PROTECTED_SHIMS:
                return False, f"AXIOLOGY_REJECT: Unauthorized modification to protected shim {fname}"
            if fname.startswith("test_") or fname.endswith("_test.py"):
                return False, f"AXIOLOGY_REJECT: Test suite tampering detected in {fname}"

        return True, "AXIOLOGY_APPROVED"


# ============================================================================
# LAYER 4: PRAXEOLOGY (Gemma 4 Action Synthesis Orchestrator)
# ============================================================================
class MOEPAGemmaAgent:
    def __init__(self, llm_client, repo_dir: Path, ontology: OntologySubstrate):
        self.llm = llm_client
        self.repo_dir = repo_dir
        self.ontology = ontology

    def solve_task(self, task: dict) -> str:
        metrology = MetrologyState(task_id=task["id"])
        seed_symbols = self._extract_initial_symbols(task["problem_statement"])

        while not metrology.budget_exhausted():
            subgraph_ctx = self.ontology.build_bounded_context(
                seed_symbols, hops=metrology.ast_hop_radius
            )

            target_file, patched_code = self._synthesize_edit(
                task["problem_statement"],
                subgraph_ctx,
                metrology.traceback_signatures[-1] if metrology.traceback_signatures else None,
            )

            if not target_file or not patched_code:
                metrology.record_and_check_stagnation("NO_EDIT_GENERATED")
                continue

            full_target_path = self.repo_dir / target_file
            self._apply_file_edit(full_target_path, patched_code)

            syntax_ok, syntax_msg = EpistemologyVerifier.verify_python_syntax(full_target_path)
            if not syntax_ok:
                self._git_reset()
                metrology.record_and_check_stagnation(syntax_msg)
                continue

            tests_ok, test_diag = EpistemologyVerifier.run_verification_tests(
                self.repo_dir, timeout_sec=metrology.remaining_seconds() * 0.5
            )
            if not tests_ok:
                self._git_reset()
                metrology.record_and_check_stagnation(test_diag)
                continue

            candidate_diff = self._get_git_diff()
            policy_ok, policy_msg = AxiologyPolicyGate.evaluate_patch_policy(candidate_diff)
            if policy_ok:
                return candidate_diff
            else:
                self._git_reset()
                metrology.record_and_check_stagnation(policy_msg)

        self._git_reset()
        return "NO_PATCH"

    def _extract_initial_symbols(self, problem_statement: str) -> List[str]:
        matched = [
            node_id for node_id in self.ontology.nodes
            if node_id.split(".")[-1] in problem_statement
        ]
        return matched[:8]

    def _synthesize_edit(self, issue: str, ctx: Dict[str, str], last_error: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        return None, None

    def _apply_file_edit(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    def _get_git_diff(self) -> str:
        res = subprocess.run(["git", "diff", "HEAD"], cwd=str(self.repo_dir), capture_output=True, text=True)
        return res.stdout.strip()

    def _git_reset(self) -> None:
        subprocess.run(["git", "checkout", "--", "."], cwd=str(self.repo_dir), capture_output=True)
        subprocess.run(["git", "clean", "-fd"], cwd=str(self.repo_dir), capture_output=True)
```

# **Part 3: Immediate 6-Day Execution Checklist**

1. **Today (Friday, Nov 6): Accept Rules on Both Pages**  
   * Log into Kaggle and accept the rules on both the Paper Track and the Main Competition. (In the event of a tie on the 0–5 Paper rubric, the paper submitted first wins the tiebreaker).  
2. **Saturday–Monday (Nov 7–9): Run a Fast Micro-Benchmark on `tasks.jsonl`**  
   * Download the public dataset (`tasks.jsonl`, `graphs/`, and `embeddings/`).  
   * Run an ablation test on 20–30 public tasks comparing Raw Gemma 4 vs. Gemma 4 \+ MOEPA Ontology/Epistemology/Axiology Gates.  
3. **Tuesday–Wednesday (Nov 10–11): Finalize the 3,000-Word Writeup & Publish Companion Notebook**  
   * Populate Section 4 with the ablation metrics.  
   * Publish a Kaggle Notebook demonstrating `MOEPAGemmaAgent` traversing the competition's AST `.json` graphs and `.npz` embeddings to qualify simultaneously for Overall Best Paper (\$15,000), Best New Application (\$10,000), and Best New Resource (\$10,000).  
4. **Thursday, Nov 12 (Before 5:59 PM CST / 11:59 PM UTC): Click Final Submit**  
   * Ensure the Kaggle Writeup is explicitly marked **Submitted**. Continue optimizing the live agent through December 2, 2026 for the \$65,000 Main Leaderboard.

