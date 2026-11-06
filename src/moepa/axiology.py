"""Layer 5: Axiology — deterministic policy and regression interlocks."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple


class AxiologyPolicyGate:
    PROTECTED_SHIMS = {"imp.py", "telnetlib.py", "pyproject.toml", "setup.cfg"}

    @classmethod
    def evaluate_patch_policy(
        cls, unified_diff: str, allow_config_edits: bool = False
    ) -> Tuple[bool, str]:
        if not unified_diff or not unified_diff.strip():
            return False, "AXIOLOGY_REJECT: Empty patch"

        modified_files = []
        for line in unified_diff.splitlines():
            if line.startswith("+++ b/"):
                modified_files.append(line[6:].strip())

        for mod_file in modified_files:
            fname = Path(mod_file).name
            if not allow_config_edits and fname in cls.PROTECTED_SHIMS:
                return False, (
                    f"AXIOLOGY_REJECT: Unauthorized modification to protected shim {fname}"
                )
            if fname.startswith("test_") or fname.endswith("_test.py"):
                return False, f"AXIOLOGY_REJECT: Test suite tampering detected in {fname}"

        return True, "AXIOLOGY_APPROVED"
