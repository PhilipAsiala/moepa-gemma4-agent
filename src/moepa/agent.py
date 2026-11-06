"""Layer 4 + orchestrator: Praxeology (Gemma 4) nested in MOEPA gates."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .axiology import AxiologyPolicyGate
from .epistemology import EpistemologyVerifier
from .metrology import MetrologyState
from .ontology import OntologySubstrate


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
                metrology.traceback_signatures[-1]
                if metrology.traceback_signatures
                else None,
            )

            if not target_file or not patched_code:
                metrology.record_and_check_stagnation("NO_EDIT_GENERATED")
                continue

            full_target_path = self.repo_dir / target_file
            self._apply_file_edit(full_target_path, patched_code)

            syntax_ok, syntax_msg = EpistemologyVerifier.verify_python_syntax(
                full_target_path
            )
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
            policy_ok, policy_msg = AxiologyPolicyGate.evaluate_patch_policy(
                candidate_diff
            )
            if policy_ok:
                return candidate_diff

            self._git_reset()
            metrology.record_and_check_stagnation(policy_msg)

        self._git_reset()
        return "NO_PATCH"

    def _extract_initial_symbols(self, problem_statement: str) -> List[str]:
        matched = [
            node_id
            for node_id in self.ontology.nodes
            if node_id.split(".")[-1] in problem_statement
        ]
        return matched[:8]

    def _synthesize_edit(
        self,
        issue: str,
        ctx: Dict[str, str],
        last_error: Optional[str],
    ) -> Tuple[Optional[str], Optional[str]]:
        # TODO: wire Gemma 4 client; return (relative_path, full_file_contents)
        _ = (issue, ctx, last_error, self.llm)
        return None, None

    def _apply_file_edit(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    def _get_git_diff(self) -> str:
        res = subprocess.run(
            ["git", "diff", "HEAD"],
            cwd=str(self.repo_dir),
            capture_output=True,
            text=True,
        )
        return res.stdout.strip()

    def _git_reset(self) -> None:
        subprocess.run(
            ["git", "checkout", "--", "."],
            cwd=str(self.repo_dir),
            capture_output=True,
        )
        subprocess.run(
            ["git", "clean", "-fd"],
            cwd=str(self.repo_dir),
            capture_output=True,
        )
