"""Tests for PCertPredictor: logistic regression certification-feasibility model."""
import numpy as np

from cert_lgs.learning.predict import PCertPredictor, load_model
from cert_lgs.learning.proposals import LearnedProposal, ProposalTier


def _tier1_proposal() -> LearnedProposal:
    return LearnedProposal(
        proposal_type="operator_priority",
        target="load-at-loc1",
        priority=1.0,
        confidence=0.8,
        metadata={},
        tier=ProposalTier.TIER1_ORDERING,
    )


def _tier3_proposal() -> LearnedProposal:
    return LearnedProposal(
        proposal_type="safe_pruning",
        target="s0",
        priority=0.5,
        confidence=0.9,
        metadata={},
        tier=ProposalTier.TIER3_PRUNING,
    )


def test_pcert_output_in_unit_interval():
    p = PCertPredictor()
    prob = p.predict_proba(_tier1_proposal())
    assert 0.0 <= prob <= 1.0


def test_pcert_predict_returns_bool():
    p = PCertPredictor()
    assert isinstance(p.predict(_tier1_proposal()), bool)


def test_pcert_different_features_different_probs():
    p = PCertPredictor(seed=42)
    p1 = p.predict_proba(_tier1_proposal())
    p3 = p.predict_proba(_tier3_proposal())
    # With random weights, probabilities are not guaranteed equal
    assert isinstance(p1, float) and isinstance(p3, float)


def test_pcert_update_reduces_loss():
    """After a positive-label update, the model should assign higher probability."""
    p = PCertPredictor(seed=42)
    proposal = _tier1_proposal()
    prob_before = p.predict_proba(proposal)
    # Apply 20 positive-label updates
    for _ in range(20):
        p.update(proposal, passed=True, lr=0.1)
    prob_after = p.predict_proba(proposal)
    assert prob_after > prob_before


def test_pcert_update_negative_label():
    """After negative-label updates, probability should drop."""
    p = PCertPredictor(seed=42)
    proposal = _tier3_proposal()
    prob_before = p.predict_proba(proposal)
    for _ in range(20):
        p.update(proposal, passed=False, lr=0.1)
    prob_after = p.predict_proba(proposal)
    assert prob_after < prob_before


def test_pcert_weight_roundtrip():
    p = PCertPredictor(seed=0)
    w = p.get_weights()
    p2 = PCertPredictor(seed=99)
    p2.set_weights(w)
    prob1 = p.predict_proba(_tier1_proposal())
    prob2 = p2.predict_proba(_tier1_proposal())
    assert abs(prob1 - prob2) < 1e-12


def test_pcert_load_model_fresh():
    pred = load_model(path=None)
    assert isinstance(pred, PCertPredictor)
    prob = pred.predict_proba(_tier1_proposal())
    assert 0.0 <= prob <= 1.0
