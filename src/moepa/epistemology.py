"""Layer 3: Epistemology — static AST checks + sandbox pytest verification."""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path
from typing import Tuple


class EpistemologyVerifier:
    @staticmethod
    def verify_python_syntax(file_path: Path) -> Tuple[bool, str]:
        try:
            source = file_path.read_text(encoding="utf-8")
            ast.parse(source, filename=str(file_path))
            return True, "SYNTAX_VALID"
        except SyntaxError as e:
            return False, f"SYNTAX_FAULT: {e.msg} at line {e.lineno}"

    @staticmethod
    def run_verification_tests(repo_dir: Path, timeout_sec: float) -> Tuple[bool, str]:
        """Offline pytest harness for Fail-to-Pass verification."""
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
