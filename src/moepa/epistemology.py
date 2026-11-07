"""Layer 3: Epistemology — static AST checks + sandbox pytest verification."""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


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
    def run_verification_tests(
        repo_dir: Path,
        timeout_sec: float,
        *,
        python_exe: Optional[str] = None,
        test_paths: Optional[Sequence[str]] = None,
        extra_env: Optional[dict] = None,
    ) -> Tuple[bool, str]:
        """Offline pytest harness for Fail-to-Pass verification.

        Prefer an isolated venv ``python_exe`` plus explicit ``test_paths``
        (from the task ``test_patch``). Falls back to bare ``pytest`` on cwd.
        """
        exe = python_exe or sys.executable
        cmd: List[str] = [exe, "-m", "pytest", "-q", "--tb=short", "--disable-warnings"]
        if test_paths:
            cmd.extend(test_paths)
        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)
        # Prefer the snapshot tree over any site-packages copy of the library.
        env["PYTHONPATH"] = str(repo_dir) + (
            os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
        )
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
                timeout=max(10.0, min(90.0, timeout_sec)),
                env=env,
            )
            if proc.returncode == 0:
                return True, "EPISTEMIC_PASS"
            lines = (proc.stdout + "\n" + proc.stderr).strip().splitlines()
            signature = "\n".join(lines[-8:]) if lines else "UNKNOWN_TEST_FAILURE"
            return False, signature
        except subprocess.TimeoutExpired:
            return False, "TIMEOUT_FAULT"
        except FileNotFoundError:
            return False, "PYTEST_MISSING"
