from __future__ import annotations

from cert_lgs.planner.types import Action, SymbolicStateSet, TransitionRelation


class TransitionSystem:
    """Explicit-state transition system supporting conditional effects.

    When initialised with a list of Action objects the system applies full
    PDDL semantics (preconditions, add/del effects, conditional effects).
    When initialised with a list of TransitionRelation objects (legacy) it
    falls back to the original string-concatenation stub for backward
    compatibility with the certification unit tests.
    """

    def __init__(self, actions_or_transitions: list):
        if actions_or_transitions and isinstance(actions_or_transitions[0], Action):
            self._actions: list[Action] = actions_or_transitions
            self._legacy_transitions: list[TransitionRelation] = []
        else:
            self._actions = []
            self._legacy_transitions = list(actions_or_transitions)

    # ------------------------------------------------------------------
    # Real PDDL-based interface
    # ------------------------------------------------------------------

    def applicable(self, atoms: frozenset[str], action: Action) -> bool:
        return action.preconditions.issubset(atoms)

    def apply(self, atoms: frozenset[str], action: Action) -> tuple[frozenset[str], float]:
        """Return (successor_atoms, cost) after applying *action* to *atoms*."""
        new_atoms = (atoms | action.add_effects) - action.del_effects
        for ce in action.conditional_effects:
            if ce.condition.issubset(atoms):
                new_atoms = (new_atoms | ce.add_atoms) - ce.del_atoms
        return frozenset(new_atoms), action.cost

    def successors(
        self, atoms: frozenset[str]
    ) -> list[tuple[str, frozenset[str], float]]:
        """Return [(action_name, successor_atoms, cost)] for all applicable actions."""
        results = []
        for action in self._actions:
            if self.applicable(atoms, action):
                succ_atoms, cost = self.apply(atoms, action)
                results.append((action.name, succ_atoms, cost))
        return results

    # ------------------------------------------------------------------
    # Legacy stub interface (used by backward-compat unit tests)
    # ------------------------------------------------------------------

    def expand(
        self, state_set: SymbolicStateSet, transition: TransitionRelation
    ) -> SymbolicStateSet:
        """Stub expand used by legacy code and backward-compat tests."""
        successor_states = frozenset(
            {f"{s}->{transition.name}" for s in state_set.states}
            or {f"init->{transition.name}"}
        )
        return SymbolicStateSet(
            name=f"{state_set.name}:{transition.name}",
            states=successor_states,
            g_cost=state_set.g_cost + transition.cost,
        )
