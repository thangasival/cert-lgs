from __future__ import annotations

from cert_lgs.certification.certificates import Certificate
from cert_lgs.planner.types import SymbolicStateSet


class PartitionChecker:
    """Checks exhaustive symbolic frontier partitioning."""

    def check_exhaustive(
        self,
        original: SymbolicStateSet,
        parts: list[SymbolicStateSet],
    ) -> Certificate:
        union = frozenset().union(*(p.states for p in parts)) if parts else frozenset()
        if union != original.states:
            return Certificate(
                name="exhaustive_partition",
                valid=False,
                reason="partition does not cover original symbolic state set",
                metadata={"original": sorted(original.states), "union": sorted(union)},
            )
        return Certificate(
            name="exhaustive_partition",
            valid=True,
            reason="partition covers original symbolic state set",
            metadata={"num_parts": len(parts)},
        )
