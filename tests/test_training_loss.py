"""Tests for the 5-term composite training loss (train.py)."""
import numpy as np
import pytest

from cert_lgs.learning.proposals import LearnedProposal, ProposalTier
from cert_lgs.learning.predict import PCertPredictor
from cert_lgs.learning.train import (
    LossBreakdown,
    LossWeights,
    TrainingEpisode,
    _calibration_loss,
    _cert_feasibility_loss,
    _diversity_bonus,
    _optimality_regularisation,
    _pairwise_ranking_loss,
    composite_loss,
    run_training_epoch,
)


def _proposals(types=("operator_priority", "safe_pruning", "operator_priority")):
    return [
        LearnedProposal(
            proposal_type=pt,
            target="s",
            priority=float(i),
            confidence=0.7,
            metadata={},
            tier=(ProposalTier.TIER3_PRUNING
                  if "pruning" in pt
                  else ProposalTier.TIER1_ORDERING),
        )
        for i, pt in enumerate(types)
    ]


def _episode() -> TrainingEpisode:
    props = _proposals()
    return TrainingEpisode(
        proposals=props,
        passed_cert=[True, False, True],
        state_g_costs=[0.0, 1.0, 2.0],
        h_star_estimates=[3.0, 2.5, 1.0],
    )


# ── individual terms ──────────────────────────────────────────────────────────

def test_ranking_loss_non_negative():
    priorities  = [1.0, 0.5, 0.2]
    g_costs     = [0.0, 1.0, 2.0]
    h_star      = [3.0, 2.0, 1.0]
    loss = _pairwise_ranking_loss(priorities, g_costs, h_star)
    assert loss >= 0.0


def test_ranking_loss_zero_for_perfect_ordering():
    """If proposals rank states in correct f=g+h* order, loss should be 0."""
    # State 0 has f=3, state 1 has f=3, state 2 has f=3: all equal → no inversions
    priorities = [3.0, 2.0, 1.0]  # descending priority = correct order
    g_costs    = [0.0, 1.0, 2.0]
    h_star     = [3.0, 2.0, 1.0]  # f = [3, 3, 3]: equal → no inversions
    loss = _pairwise_ranking_loss(priorities, g_costs, h_star)
    assert loss == 0.0


def test_ranking_loss_with_none_hstar():
    """Missing h* estimates are skipped without raising."""
    priorities = [1.0, 0.5]
    g_costs    = [0.0, 1.0]
    h_star     = [None, None]
    loss = _pairwise_ranking_loss(priorities, g_costs, h_star)
    assert loss == 0.0


def test_cert_feasibility_loss_non_negative():
    props  = _proposals()
    passed = [True, False, True]
    probs  = [0.9, 0.1, 0.8]
    loss = _cert_feasibility_loss(props, passed, probs)
    assert loss >= 0.0


def test_cert_feasibility_loss_perfect():
    """Perfect predictions → very low cross-entropy."""
    props  = _proposals()
    passed = [True, False, True]
    probs  = [0.999, 0.001, 0.999]
    loss = _cert_feasibility_loss(props, passed, probs)
    assert loss < 0.02


def test_calibration_loss_perfect():
    """Perfect calibration → ECE ≈ 0."""
    confidences = [0.1] * 10 + [0.9] * 10
    passed      = [False] * 10 + [True] * 10
    ece = _calibration_loss(confidences, passed)
    assert ece < 0.15


def test_diversity_bonus_in_unit_interval():
    props = _proposals(("operator_priority", "safe_pruning", "bdd_partition"))
    bonus = _diversity_bonus(props)
    assert 0.0 <= bonus <= 1.0


def test_diversity_bonus_zero_for_single_type():
    props = _proposals(("operator_priority", "operator_priority"))
    bonus = _diversity_bonus(props)
    assert bonus == pytest.approx(0.0, abs=1e-9)


def test_diversity_bonus_higher_with_more_types():
    mono  = _proposals(("operator_priority",) * 4)
    mixed = _proposals(("operator_priority", "safe_pruning", "bdd_partition", "admissible_bound_substitution"))
    assert _diversity_bonus(mixed) > _diversity_bonus(mono)


def test_optimality_reg_non_negative():
    props   = _proposals(("safe_pruning", "operator_priority"))
    passed  = [True, True]
    h_star  = [0.5, 2.0]
    g_costs = [3.0, 0.0]
    loss = _optimality_regularisation(props, passed, h_star, g_costs)
    assert loss >= 0.0


# ── composite loss ────────────────────────────────────────────────────────────

def test_composite_loss_returns_breakdown():
    ep   = _episode()
    pred = PCertPredictor(seed=42)
    probs = [pred.predict_proba(p) for p in ep.proposals]
    bd = composite_loss(ep, probs)
    assert isinstance(bd, LossBreakdown)
    assert np.isfinite(bd.total)
    assert np.isfinite(bd.L1_ranking)
    assert np.isfinite(bd.L2_cert)
    assert np.isfinite(bd.L3_cal)
    assert np.isfinite(bd.L4_opt)
    assert np.isfinite(bd.L5_div)


def test_composite_loss_as_dict():
    ep   = _episode()
    pred = PCertPredictor(seed=42)
    probs = [pred.predict_proba(p) for p in ep.proposals]
    d = composite_loss(ep, probs).as_dict()
    assert set(d.keys()) == {"total", "L1_ranking", "L2_cert", "L3_cal", "L4_opt", "L5_div_bonus"}


def test_composite_loss_custom_weights():
    ep   = _episode()
    pred = PCertPredictor(seed=42)
    probs = [pred.predict_proba(p) for p in ep.proposals]
    w1 = LossWeights(ranking=0.0, cert_feas=1.0, calibration=0.0,
                     optimality=0.0, diversity=0.0)
    bd1 = composite_loss(ep, probs, weights=w1)
    assert bd1.total == pytest.approx(bd1.L2_cert, rel=1e-6)


# ── training epoch ────────────────────────────────────────────────────────────

def test_run_training_epoch_returns_dict():
    pred = PCertPredictor(seed=42)
    avg = run_training_epoch([_episode()], pred)
    assert "total" in avg
    assert np.isfinite(avg["total"])


def test_run_training_epoch_empty():
    pred = PCertPredictor(seed=42)
    avg = run_training_epoch([], pred)
    assert avg["total"] == 0.0


def test_training_updates_weights():
    pred = PCertPredictor(seed=42)
    w_before = pred.get_weights().copy()
    run_training_epoch([_episode(), _episode()], pred, lr=0.1)
    assert not np.allclose(pred.get_weights(), w_before)
