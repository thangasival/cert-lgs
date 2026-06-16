from pathlib import Path

from cert_lgs.certification.certifier import CertificationLayer
from cert_lgs.learning.model import AdversarialRanker, HeuristicRanker
from cert_lgs.planner.symbolic_search import SymbolicSearchPlanner


CONFIG = {
    "benchmark": {"domains": ["benchmarks/toy_expressive"]},
    "certification": {"pruning_confidence_threshold": 0.75},
    "learning": {"model_type": "heuristic_ranker"},
}


def _make_planner():
    return SymbolicSearchPlanner(CONFIG)


def _make_certifier():
    return CertificationLayer(CONFIG)


def test_search_finds_plan():
    planner = _make_planner()
    result = planner.solve_with_guidance(HeuristicRanker(), _make_certifier())
    assert result.status == "solved"
    assert result.plan is not None
    assert result.plan_cost is not None


def test_search_optimal_cost():
    planner = _make_planner()
    result = planner.solve_with_guidance(HeuristicRanker(), _make_certifier())
    # Optimal plan: load(1) + move(2) + deliver(1) = 4.
    assert result.plan_cost == 4.0


def test_search_plan_steps():
    planner = _make_planner()
    result = planner.solve_with_guidance(HeuristicRanker(), _make_certifier())
    assert result.plan is not None
    step_names = [s.action for s in result.plan.steps]
    assert step_names == ["load-at-loc1", "move-loc1-to-loc2", "deliver-at-loc2"]


def test_adversarial_model_produces_solved_plan():
    """Adversarial model must not prevent the planner from finding a solution."""
    planner = _make_planner()
    result = planner.solve_with_guidance(AdversarialRanker(), _make_certifier())
    assert result.status == "solved"
    assert result.plan_cost == 4.0


def test_adversarial_model_pruning_rejected():
    """All unsafe_pruning_attempt proposals must be rejected by the certifier."""
    planner = _make_planner()
    certifier = _make_certifier()
    planner.solve_with_guidance(AdversarialRanker(), certifier)
    pruning_events = [
        e for e in certifier.events
        if e["certificate"] in ("safe_pruning", "admissible_bound_pruning")
        and not e["valid"]
    ]
    assert len(pruning_events) >= 1
