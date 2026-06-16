from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProposalTier(str, Enum):
    TIER1_ORDERING = "tier1_ordering"
    TIER2_STRUCTURAL = "tier2_structural"
    TIER3_PRUNING = "tier3_pruning"


@dataclass(frozen=True)
class LearnedProposal:
    proposal_type: str
    target: str
    priority: float
    confidence: float
    metadata: dict[str, Any]
    tier: str = ProposalTier.TIER1_ORDERING  # default: ordering (always safe)


@dataclass
class CertifiedProposalQueue:
    proposals: list[LearnedProposal]

    def select_state(self, open_list):
        """Select the open state with the lowest g-cost (UCS).

        Certified ordering proposals adjust transition priority but not state
        selection in the current implementation.
        """
        if not open_list:
            raise ValueError("select_state called on empty open list")
        return min(open_list, key=lambda s: s.g_cost)

    def select_transition(self, transitions):
        """Return the highest-priority transition according to accepted proposals."""
        if not self.proposals:
            return transitions[0]
        ranked = sorted(self.proposals, key=lambda p: p.priority, reverse=True)
        for proposal in ranked:
            for transition in transitions:
                if transition.name == proposal.target:
                    return transition
        return transitions[0]
