"""Layer 1: Metrology — telemetry, compute budgeting, loop-stagnation detection."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List


@dataclass
class MetrologyState:
    task_id: str
    max_wall_seconds: float = 270.0  # keeps ~120 tasks under a 12h global wall
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
        """Record diagnostics; expand Ontology hop radius if stuck. Returns True if stagnating."""
        self.cycle_count += 1
        self.traceback_signatures.append(tb_signature)
        if len(self.traceback_signatures) >= 2:
            if self.traceback_signatures[-1] == self.traceback_signatures[-2]:
                self.ast_hop_radius = min(3, self.ast_hop_radius + 1)
                return True
        return False
