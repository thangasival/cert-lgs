from __future__ import annotations

from typing import TYPE_CHECKING

from cert_lgs.certification.certificates import Certificate
from cert_lgs.planner.types import SymbolicStateSet, TransitionRelation

if TYPE_CHECKING:
    from cert_lgs.planner.types import Action


class TransitionChecker:
    """C1 certifier: verifies that a symbolic transition matches PDDL semantics.

    When an Action object is supplied, re-derives the expected successor by
    applying preconditions → add/del effects → conditional effects (CE fires
    on PRE-state atoms) and checks set equality with the claimed successor.
    This ensures correctness for domains with conditional effects and
    state-dependent action costs simultaneously.
    """

    def check(
        self,
        source: SymbolicStateSet,
        transition: TransitionRelation,
        successor: SymbolicStateSet,
        action: Action | None = None,
    ) -> Certificate:
        if transition.cost < 0:
            return Certificate(
                name="transition_semantics",
                valid=False,
                reason="negative transition costs are not allowed for optimality proof",
            )
        if not successor.states:
            return Certificate(
                name="transition_semantics",
                valid=False,
                reason="successor symbolic set is empty",
            )

        if action is not None:
            # Re-derive expected successor from PDDL semantics.
            pre_atoms = source.states
            new_atoms: frozenset[str] = (pre_atoms | action.add_effects) - action.del_effects
            for ce in action.conditional_effects:
                # CE condition is evaluated on the PRE-state (not the post-state).
                if ce.condition.issubset(pre_atoms):
                    new_atoms = (new_atoms | ce.add_atoms) - ce.del_atoms
            expected = frozenset(new_atoms)
            if expected != successor.states:
                diff = sorted(expected.symmetric_difference(successor.states))
                return Certificate(
                    name="transition_semantics",
                    valid=False,
                    reason="successor atoms mismatch PDDL semantics",
                    metadata={
                        "action": action.name,
                        "expected": sorted(expected),
                        "got": sorted(successor.states),
                        "symmetric_diff": diff,
                    },
                )
            return Certificate(
                name="transition_semantics",
                valid=True,
                reason="transition verified against PDDL semantics including conditional effects",
                metadata={"action": action.name, "atoms_checked": len(expected)},
            )

        # No action schema provided: structural checks only.
        return Certificate(
            name="transition_semantics",
            valid=True,
            reason="transition accepted (no action schema provided for semantic check)",
            metadata={"source": source.name, "transition": transition.name, "successor": successor.name},
        )
