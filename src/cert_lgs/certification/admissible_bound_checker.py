from __future__ import annotations

from cert_lgs.certification.certificates import Certificate
from cert_lgs.planner.types import SymbolicStateSet


class AdmissibleBoundChecker:
    """C3 certifier: constructs h_safe = min(h_L, h_cert) for admissible pruning.

    h_cert is a goal-reachable lower bound: if the goal is not yet satisfied in
    the current state, at least one more action of cost >= min_action_cost is
    required.  This is admissible by construction.

    Call set_task_info() once before search to enable non-trivial h_cert; without
    it the checker falls back to h_cert = 0.0 (sound but vacuous, backward-
    compatible with tests that don't inject task info).
    """

    def __init__(self) -> None:
        self._goal_atoms: frozenset[str] | None = None
        self._min_action_cost: float = 1.0

    # ------------------------------------------------------------------
    # Task injection (called by CertificationLayer.set_task)
    # ------------------------------------------------------------------

    def set_task_info(self, goal_atoms: frozenset[str], min_action_cost: float) -> None:
        """Provide goal atoms and minimum action cost for h_cert computation."""
        self._goal_atoms = goal_atoms
        self._min_action_cost = max(min_action_cost, 1e-9)

    # ------------------------------------------------------------------
    # h_cert: goal-reachable admissible lower bound
    # ------------------------------------------------------------------

    def certified_bound(self, state_set: SymbolicStateSet) -> float:
        """Return h_cert(state_set): admissible lower bound on remaining cost.

        h_cert = 0          if the goal is already satisfied
        h_cert = min_cost   if at least one goal atom is unsatisfied
                            (reaching any unsatisfied goal needs >= 1 action
                             of cost >= min_action_cost)
        h_cert = 0          if no goal info available (fallback)
        """
        if self._goal_atoms is None or not self._goal_atoms:
            return 0.0
        if self._goal_atoms.issubset(state_set.states):
            return 0.0
        return self._min_action_cost

    # ------------------------------------------------------------------
    # h_safe = min(h_L, h_cert)
    # ------------------------------------------------------------------

    def safe_bound(
        self,
        state_set: SymbolicStateSet,
        learned_estimate: float | None = None,
    ) -> float:
        h_cert = self.certified_bound(state_set)
        if learned_estimate is None:
            return h_cert
        return min(h_cert, learned_estimate)

    # ------------------------------------------------------------------
    # Pruning certificate: g(S) + h_safe(S) >= C_inc
    # ------------------------------------------------------------------

    def check_pruning_bound(
        self,
        state_set: SymbolicStateSet,
        incumbent_cost: float,
        learned_estimate: float | None = None,
    ) -> Certificate:
        bound = self.safe_bound(state_set, learned_estimate)
        if state_set.g_cost + bound >= incumbent_cost:
            return Certificate(
                name="admissible_bound_pruning",
                valid=True,
                reason="certified lower bound permits pruning",
                metadata={
                    "g": state_set.g_cost,
                    "h_safe": bound,
                    "h_cert": self.certified_bound(state_set),
                    "incumbent": incumbent_cost,
                },
            )
        return Certificate(
            name="admissible_bound_pruning",
            valid=False,
            reason="certified lower bound does not permit pruning",
            metadata={
                "g": state_set.g_cost,
                "h_safe": bound,
                "h_cert": self.certified_bound(state_set),
                "incumbent": incumbent_cost,
            },
        )
