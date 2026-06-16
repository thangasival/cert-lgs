from __future__ import annotations

from dataclasses import dataclass

from cert_lgs.planner.types import AxiomRule


@dataclass(frozen=True)
class ExpressiveFeatureFlags:
    conditional_effects: bool = True
    axioms: bool = True
    state_dependent_costs: bool = True


class ExpressiveSemantics:
    """Semantics hooks for expressive planning features."""

    def __init__(
        self,
        flags: ExpressiveFeatureFlags,
        axiom_rules: list[AxiomRule] | None = None,
    ):
        self.flags = flags
        self._axiom_rules: list[AxiomRule] = axiom_rules or []

    def set_axiom_rules(self, rules: list[AxiomRule]) -> None:
        self._axiom_rules = rules

    def evaluate_conditional_effects(
        self,
        state: frozenset[str],
        action_cond_effects,
    ) -> tuple[frozenset[str], frozenset[str]]:
        """Return (add_atoms, del_atoms) from triggered conditional effects.

        *action_cond_effects* is the ``conditional_effects`` tuple from an
        ``Action`` dataclass.  The pre-state *state* is the set of atoms before
        the action's unconditional effects are applied.
        """
        if not self.flags.conditional_effects:
            return frozenset(), frozenset()
        add: set[str] = set()
        delete: set[str] = set()
        for ce in action_cond_effects:
            if ce.condition <= state:
                add.update(ce.add_atoms)
                delete.update(ce.del_atoms)
        return frozenset(add), frozenset(delete)

    def close_axioms(self, atoms: frozenset[str]) -> frozenset[str]:
        """Least-fixed-point axiom closure.

        Iteratively fire any :derived rule whose body is satisfied by the
        current atom set, adding the rule head until no new atoms are derived.
        """
        if not self.flags.axioms or not self._axiom_rules:
            return atoms
        current: set[str] = set(atoms)
        changed = True
        while changed:
            changed = False
            for rule in self._axiom_rules:
                if rule.head not in current and rule.body <= current:
                    current.add(rule.head)
                    changed = True
        return frozenset(current)

    def state_dependent_cost(
        self,
        state: frozenset[str],
        base_cost: float = 1.0,
    ) -> float:
        """Return the action cost in *state*.

        Currently returns *base_cost* unchanged; override or extend for EVMDD
        state-dependent cost expressions when full SAS+ encoding is available.
        """
        if not self.flags.state_dependent_costs:
            return base_cost
        return base_cost
