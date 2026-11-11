"""Layer 4 + orchestrator: Praxeology (Gemma 4) nested in MOEPA gates."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .axiology import AxiologyPolicyGate
from .epistemology import EpistemologyVerifier
from .metrology import MetrologyState
from .ontology import OntologySubstrate

SYSTEM = (
    "You are a careful software-engineering agent. "
    "Edit exactly one existing Python source file to fix the issue. "
    "Reply with one JSON object and no other text. "
    'Schema: {"path": "relative/path.py", "content": "<full new file contents>", "abstain": false}. '
    "If you cannot produce a safe edit, set abstain to true and content to an empty string. "
    "Do not modify tests. Do not invent files that are not in the provided neighborhood."
)


class MOEPAGemmaAgent:
    def __init__(
        self,
        llm_client,
        repo_dir: Path,
        ontology: OntologySubstrate,
        *,
        context_chars: int = 8000,
        snippet_chars: int = 1200,
        run_pytest: bool = True,
    ):
        self.llm = llm_client
        self.repo_dir = Path(repo_dir)
        self.ontology = ontology
        self.context_chars = context_chars
        self.snippet_chars = snippet_chars
        self.run_pytest = run_pytest

    def solve_task(self, task: dict) -> str:
        task_id = task.get("id") or task.get("instance_id") or "task"
        metrology = MetrologyState(task_id=str(task_id))
        problem = task.get("problem_statement") or task.get("issue") or ""
        seed_symbols = self._extract_initial_symbols(problem)

        while not metrology.budget_exhausted():
            subgraph_ctx = self.ontology.build_bounded_context(
                seed_symbols, hops=metrology.ast_hop_radius
            )

            target_file, patched_code = self._synthesize_edit(
                problem,
                subgraph_ctx,
                metrology.traceback_signatures[-1]
                if metrology.traceback_signatures
                else None,
            )

            if not target_file or not patched_code:
                metrology.record_and_check_stagnation("NO_EDIT_GENERATED")
                continue

            full_target_path = self.repo_dir / target_file
            if not full_target_path.exists():
                metrology.record_and_check_stagnation(f"MISSING_FILE:{target_file}")
                continue

            # Ontological boundary (enforced): a patch that reads a name
            # neither defined in the file, a builtin, nor in G_sub is
            # rejected before it is applied — and therefore before any test
            # runs. Rejection records stagnation, so a repeated failure
            # widens the neighborhood (Metrology pivot).
            offenders = self.ontology.reject_out_of_neighborhood(
                patched_code,
                set(subgraph_ctx) | set(seed_symbols),
            )
            if offenders:
                metrology.record_and_check_stagnation(
                    "OUT_OF_NEIGHBORHOOD: " + ", ".join(offenders[:8])
                )
                continue

            self._apply_file_edit(full_target_path, patched_code)

            syntax_ok, syntax_msg = EpistemologyVerifier.verify_python_syntax(
                full_target_path
            )
            if not syntax_ok:
                self._git_reset()
                metrology.record_and_check_stagnation(syntax_msg)
                continue

            if self.run_pytest:
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
        return self.ontology.seed_symbols_from_text(problem_statement, limit=8)

    def _pack_context(self, ctx: Dict[str, str]) -> str:
        parts = []
        used = 0
        for nid, text in ctx.items():
            piece = f"### {nid}\n{text[: self.snippet_chars]}\n"
            if used + len(piece) > self.context_chars:
                break
            parts.append(piece)
            used += len(piece)
        return "".join(parts)

    def _synthesize_edit(
        self,
        issue: str,
        ctx: Dict[str, str],
        last_error: Optional[str],
    ) -> Tuple[Optional[str], Optional[str]]:
        if self.llm is None:
            return None, None
        prompt = f"Issue:\n{issue[:4000]}\n\nCode neighborhood:\n{self._pack_context(ctx)}\n"
        if last_error:
            prompt += f"\nPrevious failure diagnostic:\n{last_error[:1500]}\n"
        prompt += "\nReturn the JSON edit object now.\n"
        if not ctx:
            return None, None
        try:
            raw = self.llm.generate(prompt, system=SYSTEM)
        except Exception as exc:  # noqa: BLE001 — surface as no-edit stagnation
            _ = exc
            return None, None
        parsed = self._parse_edit(raw)
        if not parsed or parsed.get("abstain"):
            return None, None
        path = str(parsed.get("path") or "").strip().lstrip("./")
        content = parsed.get("content")
        if not path or not isinstance(content, str) or not content.strip():
            return None, None
        return path, content

    @staticmethod
    def _parse_edit(text: str) -> Optional[dict]:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            return None
        try:
            obj = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
        return obj if isinstance(obj, dict) else None

    def _apply_file_edit(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
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
