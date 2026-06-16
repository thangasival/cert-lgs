from __future__ import annotations

from cert_lgs.certification.certificates import Certificate
from cert_lgs.planner.types import SymbolicStateSet


class PruningChecker:
    """Approves pruning only with symbolic evidence."""

    def check_dominance(
        self,
        candidate: SymbolicStateSet,
        closed: list[SymbolicStateSet],
    ) -> Certificate:
        for seen in closed:
            if candidate.states.issubset(seen.states) and seen.g_cost <= candidate.g_cost:
                return Certificate(
                    name="dominance_pruning",
                    valid=True,
                    reason="candidate dominated by closed symbolic state set",
                    metadata={"candidate": candidate.name, "dominator": seen.name},
                )
        return Certificate(
            name="dominance_pruning",
            valid=False,
            reason="no dominance certificate found",
        )
