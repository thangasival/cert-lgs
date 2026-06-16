"""Tests for build_guidance_model() factory function."""
import numpy as np
import pytest

from cert_lgs.learning.model import (
    AdversarialRanker,
    GNNRanker,
    GuidanceModel,
    HeuristicRanker,
    build_guidance_model,
)


def test_factory_default_is_heuristic_ranker():
    model = build_guidance_model({})
    assert isinstance(model, HeuristicRanker)


def test_factory_explicit_heuristic_ranker():
    model = build_guidance_model({"learning": {"model_type": "heuristic_ranker"}})
    assert isinstance(model, HeuristicRanker)


def test_factory_gnn_ranker():
    model = build_guidance_model({"learning": {"model_type": "gnn_ranker"}})
    assert isinstance(model, GNNRanker)


def test_factory_gnn_ranker_with_seed():
    model = build_guidance_model({"learning": {"model_type": "gnn_ranker", "seed": 7}})
    assert isinstance(model, GNNRanker)


def test_factory_adversarial_ranker():
    model = build_guidance_model({"learning": {"model_type": "adversarial_ranker"}})
    assert isinstance(model, AdversarialRanker)


def test_factory_unknown_type_falls_back_to_heuristic():
    model = build_guidance_model({"learning": {"model_type": "nonexistent_model"}})
    assert isinstance(model, HeuristicRanker)


def test_factory_all_models_are_guidance_model_subclasses():
    for cfg in [
        {},
        {"learning": {"model_type": "heuristic_ranker"}},
        {"learning": {"model_type": "gnn_ranker"}},
        {"learning": {"model_type": "adversarial_ranker"}},
    ]:
        assert isinstance(build_guidance_model(cfg), GuidanceModel)


def test_factory_gnn_seed_controls_weights():
    m1 = build_guidance_model({"learning": {"model_type": "gnn_ranker", "seed": 42}})
    m2 = build_guidance_model({"learning": {"model_type": "gnn_ranker", "seed": 42}})
    m3 = build_guidance_model({"learning": {"model_type": "gnn_ranker", "seed": 99}})
    np.testing.assert_array_equal(m1.W1, m2.W1)
    assert not np.array_equal(m1.W1, m3.W1)


def test_factory_gnn_default_seed_is_42():
    m_default = build_guidance_model({"learning": {"model_type": "gnn_ranker"}})
    m_seed42  = build_guidance_model({"learning": {"model_type": "gnn_ranker", "seed": 42}})
    np.testing.assert_array_equal(m_default.W1, m_seed42.W1)
