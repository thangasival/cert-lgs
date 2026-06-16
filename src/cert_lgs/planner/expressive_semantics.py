from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExpressiveFeatureFlags:
    conditional_effects: bool = True
    axioms: bool = True
    state_dependent_costs: bool = True


class ExpressiveSemantics:
    """Semantics hooks for expressive planning features."""

    def __init__(self, flags: ExpressiveFeatureFlags):
        self.flags = flags

    def evaluate_conditional_effects(self, state: str, action: str) -> set[str]:
        return {f"effect({action})@{state}"}

    def close_axioms(self, atoms: set[str]) -> set[str]:
        if not self.flags.axioms:
            return atoms
        return set(atoms) | {f"derived({a})" for a in atoms if a.startswith("effect")}

    def state_dependent_cost(self, state: str, action: str, base_cost: float = 1.0) -> float:
        if not self.flags.state_dependent_costs:
            return base_cost
        return base_cost
