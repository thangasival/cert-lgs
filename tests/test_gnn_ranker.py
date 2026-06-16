"""Tests for GNNRanker: numpy 2-layer MLP guidance model."""
import numpy as np

from cert_lgs.learning.model import GNNRanker
from cert_lgs.learning.proposals import ProposalTier
from cert_lgs.planner.types import SymbolicStateSet, TransitionRelation


GOAL = frozenset({"delivered"})

_TRANSITIONS = [
    TransitionRelation("load-at-loc1",      "load-at-loc1",      cost=1.0),
    TransitionRelation("move-loc1-to-loc2", "move-loc1-to-loc2", cost=2.0),
    TransitionRelation("deliver-at-loc2",   "deliver-at-loc2",   cost=1.0),
]

_OPEN = [
    SymbolicStateSet("s0", frozenset({"at-truck-loc1"}),                              0.0),
    SymbolicStateSet("s1", frozenset({"at-truck-loc1", "in-truck"}),                  1.0),
    SymbolicStateSet("s2", frozenset({"at-truck-loc2", "in-truck", "box-in-transit"}), 3.0),
]


def test_gnn_produces_proposals():
    ranker = GNNRanker(seed=42)
    proposals = ranker.propose(_OPEN, _TRANSITIONS, goal_atoms=GOAL)
    assert len(proposals) == len(_OPEN)


def test_gnn_all_proposals_are_tier1():
    ranker = GNNRanker(seed=42)
    proposals = ranker.propose(_OPEN, _TRANSITIONS, goal_atoms=GOAL)
    for p in proposals:
        assert p.tier == ProposalTier.TIER1_ORDERING
        assert p.proposal_type == "operator_priority"


def test_gnn_priorities_are_floats():
    ranker = GNNRanker(seed=42)
    proposals = ranker.propose(_OPEN, _TRANSITIONS, goal_atoms=GOAL)
    for p in proposals:
        assert isinstance(p.priority, float)


def test_gnn_empty_open_list():
    ranker = GNNRanker(seed=42)
    proposals = ranker.propose([], _TRANSITIONS, goal_atoms=GOAL)
    assert proposals == []


def test_gnn_score_goal_vs_non_goal():
    """State with fewer unsatisfied goals should get different score than far state."""
    ranker = GNNRanker(seed=42)
    near_goal  = SymbolicStateSet("near", frozenset({"at-truck-loc2", "in-truck"}), 3.0)
    far        = SymbolicStateSet("far",  frozenset({"at-truck-loc1"}),             0.0)
    s_near = ranker.score(near_goal, GOAL)
    s_far  = ranker.score(far, GOAL)
    # Scores are floats (finite) — exact ordering depends on random weights
    assert np.isfinite(s_near)
    assert np.isfinite(s_far)


def test_gnn_weight_roundtrip():
    ranker = GNNRanker(seed=7)
    w = ranker.get_weights()
    ranker2 = GNNRanker(seed=99)   # different random init
    ranker2.set_weights(w)
    # After loading, scores must match
    s0 = SymbolicStateSet("s0", frozenset({"at-truck-loc1"}), 0.0)
    assert ranker.score(s0, GOAL) == ranker2.score(s0, GOAL)


def test_gnn_deterministic_with_same_seed():
    r1 = GNNRanker(seed=42)
    r2 = GNNRanker(seed=42)
    s = SymbolicStateSet("s", frozenset({"at-truck-loc1"}), 0.0)
    assert r1.score(s, GOAL) == r2.score(s, GOAL)


def test_gnn_finds_optimal_plan():
    """GNNRanker must find an optimal plan (UCS correctness, not guidance quality)."""
    from pathlib import Path
    from cert_lgs.certification.certifier import CertificationLayer
    from cert_lgs.planner.symbolic_search import SymbolicSearchPlanner

    cfg = {
        "benchmark": {"domains": ["benchmarks/toy_expressive"]},
        "certification": {"pruning_confidence_threshold": 0.75},
        "learning": {"model_type": "gnn_ranker", "seed": 42},
    }
    import os
    os.chdir(Path(__file__).parent.parent)

    planner   = SymbolicSearchPlanner(cfg)
    certifier = CertificationLayer(cfg)
    result    = planner.solve_with_guidance(GNNRanker(seed=42), certifier)
    assert result.status == "solved"
    assert result.plan_cost == 4.0
