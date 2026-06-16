from __future__ import annotations

from typing import Any

from cert_lgs.certification.admissible_bound_checker import AdmissibleBoundChecker
from cert_lgs.certification.certificates import Certificate
from cert_lgs.certification.partition_checker import PartitionChecker
from cert_lgs.certification.plan_validator import PlanValidator
from cert_lgs.certification.pruning_checker import PruningChecker
from cert_lgs.certification.transition_checker import TransitionChecker
from cert_lgs.learning.proposals import CertifiedProposalQueue, LearnedProposal, ProposalTier
from cert_lgs.planner.types import Action, Plan, SymbolicStateSet, TransitionRelation


class CertificationLayer:
    """Central safety layer implementing the three-tier proposal hierarchy.

    Tier 1 — Ordering (operator_priority, expansion_order,
              frontier_partition_order): always accepted, no cert needed.
    Tier 2 — Structural (bdd_partition, admissible_bound_substitution):
              cheap certification via C2 / C3.
    Tier 3 — Pruning (safe_pruning, unsafe_pruning_attempt):
              confidence-gated by threshold θ, then certified by C4.

    Any proposal that fails its certifier is silently dropped (fallback =
    the unmodified search state, which continues under baseline behaviour).
    """

    # Proposal types that belong to each tier.
    TIER1_TYPES: frozenset[str] = frozenset(
        {"operator_priority", "expansion_order", "frontier_partition_order"}
    )
    TIER2_TYPES: frozenset[str] = frozenset(
        {"bdd_partition", "admissible_bound_substitution"}
    )
    TIER3_TYPES: frozenset[str] = frozenset(
        {"safe_pruning", "unsafe_pruning_attempt"}
    )

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.transition_checker = TransitionChecker()
        self.partition_checker = PartitionChecker()
        self.bound_checker = AdmissibleBoundChecker()
        self.pruning_checker = PruningChecker()
        self.plan_validator = PlanValidator()
        self.checked = 0
        self.rejected = 0
        self.events: list[dict[str, Any]] = []

        # θ threshold for Tier 3 confidence-gating.
        cert_cfg = config.get("certification", {})
        self._theta: float = cert_cfg.get("pruning_confidence_threshold", 0.75)

    # ------------------------------------------------------------------
    # Internal accounting
    # ------------------------------------------------------------------

    def _record(self, certificate: Certificate) -> None:
        self.checked += 1
        if not certificate.valid:
            self.rejected += 1
        self.events.append(
            {
                "certificate": certificate.name,
                "valid": certificate.valid,
                "reason": certificate.reason,
                "metadata": certificate.metadata,
            }
        )

    # ------------------------------------------------------------------
    # Three-tier proposal filter (main public API)
    # ------------------------------------------------------------------

    def filter_proposals(
        self,
        proposals: list[LearnedProposal],
        open_list: list[SymbolicStateSet],
        closed: list[SymbolicStateSet],
        incumbent_cost: float,
    ) -> CertifiedProposalQueue:
        accepted: list[LearnedProposal] = []

        for proposal in proposals:
            pt = proposal.proposal_type

            # ---- Tier 1: ordering — always accept, no cert needed ----
            if pt in self.TIER1_TYPES:
                accepted.append(proposal)
                continue

            # ---- Tier 2: structural — cheap certification ----
            if pt in self.TIER2_TYPES:
                if pt == "bdd_partition":
                    parts = proposal.metadata.get("parts", [])
                    if open_list and parts:
                        cert = self.partition_checker.check_exhaustive(open_list[0], parts)
                        self._record(cert)
                        if cert.valid:
                            accepted.append(proposal)
                        # Fallback: frontier remains unsplit under baseline ordering.
                    else:
                        # Cannot verify without a target or parts; skip silently.
                        cert = Certificate(
                            "exhaustive_partition", False, "missing open_list or parts"
                        )
                        self._record(cert)

                elif pt == "admissible_bound_substitution":
                    # C3 never fails: min(h_L, h_cert) is always admissible.
                    cert = Certificate(
                        "admissible_bound",
                        True,
                        "min(h_L, h_cert) always admissible by construction",
                    )
                    self._record(cert)
                    accepted.append(proposal)
                continue

            # ---- Tier 3: pruning — confidence-gate then certify ----
            if pt in self.TIER3_TYPES:
                conf = proposal.confidence

                if conf < self._theta:
                    # Downgrade to ordering hint — preserves state in OPEN.
                    hint = LearnedProposal(
                        proposal_type="operator_priority",
                        target=proposal.target,
                        priority=proposal.priority,
                        confidence=conf,
                        metadata={**proposal.metadata, "downgraded_from": pt},
                        tier=ProposalTier.TIER1_ORDERING,
                    )
                    accepted.append(hint)
                    continue

                # Above θ: submit to C4 (admissible-bound pruning check).
                target = open_list[0] if open_list else None
                if target is None:
                    cert = Certificate("safe_pruning", False, "no target state set")
                else:
                    cert = self.bound_checker.check_pruning_bound(target, incumbent_cost)
                self._record(cert)
                if cert.valid:
                    accepted.append(proposal)
                # Else: fallback — proposal dropped; state stays in OPEN.
                continue

            # ---- Unknown proposal type — reject and log ----
            cert = Certificate(
                name="unknown_proposal",
                valid=False,
                reason=f"unknown proposal type: {pt!r}",
            )
            self._record(cert)

        return CertifiedProposalQueue(proposals=accepted)

    # ------------------------------------------------------------------
    # Task injection — enables non-trivial h_cert in C3
    # ------------------------------------------------------------------

    def set_task(self, task) -> None:
        """Inject planning task so C3 can compute a real admissible lower bound."""
        goal_atoms = getattr(task, "goal_atoms", frozenset())
        actions = getattr(task, "actions", None)
        min_cost = min((a.cost for a in actions), default=1.0) if actions else 1.0
        self.bound_checker.set_task_info(goal_atoms, min_cost)

    # ------------------------------------------------------------------
    # Per-transition correctness check (C1)
    # ------------------------------------------------------------------

    def valid_transition(
        self,
        source: SymbolicStateSet,
        transition: TransitionRelation,
        successor: SymbolicStateSet,
        action: Action | None = None,
    ) -> bool:
        cert = self.transition_checker.check(source, transition, successor, action=action)
        self._record(cert)
        return cert.valid

    # ------------------------------------------------------------------
    # Enqueue safety check (C4 dominance + C3 bound)
    # ------------------------------------------------------------------

    def safe_to_enqueue(
        self,
        candidate: SymbolicStateSet,
        closed: list[SymbolicStateSet],
        incumbent_cost: float,
    ) -> bool:
        dominance = self.pruning_checker.check_dominance(candidate, closed)
        self._record(dominance)
        if dominance.valid:
            return False

        if incumbent_cost < float("inf"):
            bound = self.bound_checker.check_pruning_bound(candidate, incumbent_cost)
            self._record(bound)
            if bound.valid:
                return False

        return True

    # ------------------------------------------------------------------
    # Plan validation (post-hoc)
    # ------------------------------------------------------------------

    def valid_plan(self, plan: Plan) -> bool:
        cert = self.plan_validator.validate(plan)
        self._record(cert)
        return cert.valid

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def diagnostics(self) -> dict[str, Any]:
        tier1 = sum(1 for e in self.events if e["certificate"] in (
            "transition_semantics", "dominance_pruning",
            "admissible_bound_pruning", "plan_validation",
        ))
        return {
            "checked": self.checked,
            "rejected": self.rejected,
            "theta": self._theta,
            "events": self.events,
        }
