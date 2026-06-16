"""Guidance models for Cert-LGS.

GuidanceModel   — abstract base class
HeuristicRanker — name-length heuristic (baseline / test stand-in)
GNNRanker       — numpy 2-layer MLP operating over state features
AdversarialRanker — intentionally wrong model for certification tests
"""
from __future__ import annotations

from typing import Any

import numpy as np

from cert_lgs.learning.proposals import LearnedProposal, ProposalTier
from cert_lgs.planner.types import SymbolicStateSet, TransitionRelation


class GuidanceModel:
    """Abstract base class for learned guidance models."""

    def propose(
        self,
        open_list: list[SymbolicStateSet],
        transitions: list[TransitionRelation],
        goal_atoms: frozenset[str] = frozenset(),
    ) -> list[LearnedProposal]:
        raise NotImplementedError


# ── Heuristic baseline ────────────────────────────────────────────────────────

class HeuristicRanker(GuidanceModel):
    """Simple heuristic ranker used as a deterministic test stand-in.

    Ranks transitions by name length (shorter first).  Produces Tier 1
    ordering proposals — always accepted with zero fallback.
    """

    def propose(
        self,
        open_list: list[SymbolicStateSet],
        transitions: list[TransitionRelation],
        goal_atoms: frozenset[str] = frozenset(),
    ) -> list[LearnedProposal]:
        sorted_transitions = sorted(transitions, key=lambda t: (len(t.name), t.name))
        proposals: list[LearnedProposal] = []
        for rank, transition in enumerate(sorted_transitions):
            proposals.append(
                LearnedProposal(
                    proposal_type="operator_priority",
                    target=transition.name,
                    priority=1.0 / (rank + 1),
                    confidence=0.75,
                    metadata={"source": "heuristic_ranker", "rank": rank},
                    tier=ProposalTier.TIER1_ORDERING,
                )
            )
        return proposals


# ── GNN-based ranker ──────────────────────────────────────────────────────────

class GNNRanker(GuidanceModel):
    """Two-layer MLP guidance model operating over state features.

    Architecture (numpy, no autograd):
        input  : 5-dim feature vector per state
        hidden : 16 neurons, tanh activation
        output : scalar priority score

    Features per state
    ------------------
    0  g_cost              accumulated path cost
    1  n_atoms             |state atoms|
    2  n_satisfied_goals   |goal ∩ state|
    3  n_unsatisfied_goals |goal \\ state|
    4  bias                constant 1.0

    The model is initialised with random weights (seed-controlled) and
    produces Tier 1 ordering proposals ranking open states by their MLP
    score.  Training is wired in train.py; inference is deterministic once
    weights are loaded.
    """

    N_FEATURES = 5
    HIDDEN_DIM = 16

    def __init__(self, seed: int = 42) -> None:
        rng = np.random.default_rng(seed)
        scale = np.sqrt(2.0 / self.N_FEATURES)
        self.W1: np.ndarray = rng.normal(0.0, scale, (self.HIDDEN_DIM, self.N_FEATURES))
        self.b1: np.ndarray = np.zeros(self.HIDDEN_DIM)
        self.W2: np.ndarray = rng.normal(0.0, scale / self.HIDDEN_DIM, (1, self.HIDDEN_DIM))
        self.b2: np.ndarray = np.zeros(1)

    # -- inference ---------------------------------------------------------

    def _features(self, sss: SymbolicStateSet, goal_atoms: frozenset[str]) -> np.ndarray:
        atoms = sss.states
        n_sat   = len(goal_atoms & atoms)
        n_unsat = len(goal_atoms - atoms)
        return np.array(
            [sss.g_cost, float(len(atoms)), float(n_sat), float(n_unsat), 1.0],
            dtype=np.float64,
        )

    def _forward(self, x: np.ndarray) -> float:
        h = np.tanh(self.W1 @ x + self.b1)
        return float((self.W2 @ h + self.b2)[0])

    def score(self, sss: SymbolicStateSet, goal_atoms: frozenset[str]) -> float:
        """Return the model's priority score for a single state."""
        return self._forward(self._features(sss, goal_atoms))

    def propose(
        self,
        open_list: list[SymbolicStateSet],
        transitions: list[TransitionRelation],
        goal_atoms: frozenset[str] = frozenset(),
    ) -> list[LearnedProposal]:
        if not open_list:
            return []
        scored = [(self.score(s, goal_atoms), s) for s in open_list]
        # Higher score → higher priority.
        scored.sort(key=lambda x: -x[0])
        return [
            LearnedProposal(
                proposal_type="operator_priority",
                target=s.name,
                priority=float(score),
                confidence=0.80,
                metadata={"source": "gnn_ranker", "rank": rank},
                tier=ProposalTier.TIER1_ORDERING,
            )
            for rank, (score, s) in enumerate(scored)
        ]

    # -- weight I/O (for future training integration) ----------------------

    def get_weights(self) -> dict[str, np.ndarray]:
        return {"W1": self.W1.copy(), "b1": self.b1.copy(),
                "W2": self.W2.copy(), "b2": self.b2.copy()}

    def set_weights(self, weights: dict[str, np.ndarray]) -> None:
        self.W1 = weights["W1"]
        self.b1 = weights["b1"]
        self.W2 = weights["W2"]
        self.b2 = weights["b2"]


# ── Adversarial model ─────────────────────────────────────────────────────────

class AdversarialRanker(GuidanceModel):
    """Intentionally wrong model for certification robustness tests.

    Proposes unsafe pruning at maximum confidence and reverses transition
    ordering.  The certification layer must reject the pruning proposal and
    accept only the (harmless) reversed ordering.
    """

    def propose(
        self,
        open_list: list[SymbolicStateSet],
        transitions: list[TransitionRelation],
        goal_atoms: frozenset[str] = frozenset(),
    ) -> list[LearnedProposal]:
        proposals: list[LearnedProposal] = [
            LearnedProposal(
                proposal_type="unsafe_pruning_attempt",
                target=open_list[0].name if open_list else "none",
                priority=999.0,
                confidence=1.0,
                metadata={"source": "adversarial_ranker", "claim": "prune_without_proof"},
                tier=ProposalTier.TIER3_PRUNING,
            )
        ]
        for transition in reversed(transitions):
            proposals.append(
                LearnedProposal(
                    proposal_type="operator_priority",
                    target=transition.name,
                    priority=100.0,
                    confidence=1.0,
                    metadata={"source": "adversarial_ranker"},
                    tier=ProposalTier.TIER1_ORDERING,
                )
            )
        return proposals


# ── Factory ───────────────────────────────────────────────────────────────────

def build_guidance_model(config: dict[str, Any]) -> GuidanceModel:
    model_type = config.get("learning", {}).get("model_type", "heuristic_ranker")
    if model_type == "adversarial_ranker":
        return AdversarialRanker()
    if model_type == "gnn_ranker":
        seed = config.get("learning", {}).get("seed", 42)
        return GNNRanker(seed=seed)
    return HeuristicRanker()
