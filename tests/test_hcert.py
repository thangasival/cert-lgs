"""Tests for the real h_cert goal-reachable admissible lower bound (C3)."""
from cert_lgs.certification.admissible_bound_checker import AdmissibleBoundChecker
from cert_lgs.planner.types import SymbolicStateSet


GOAL = frozenset({"delivered"})
MIN_COST = 1.0


def _checker() -> AdmissibleBoundChecker:
    c = AdmissibleBoundChecker()
    c.set_task_info(GOAL, MIN_COST)
    return c


def test_hcert_zero_at_goal():
    checker = _checker()
    goal_state = SymbolicStateSet("g", frozenset({"delivered", "at-truck-loc2"}), 4.0)
    assert checker.certified_bound(goal_state) == 0.0


def test_hcert_nonzero_before_goal():
    checker = _checker()
    non_goal = SymbolicStateSet("s", frozenset({"at-truck-loc1"}), 0.0)
    assert checker.certified_bound(non_goal) == MIN_COST


def test_hcert_equals_min_cost_for_all_non_goal_states():
    checker = _checker()
    states = [
        SymbolicStateSet("s0", frozenset({"at-truck-loc1"}), 0.0),
        SymbolicStateSet("s1", frozenset({"at-truck-loc1", "in-truck"}), 1.0),
        SymbolicStateSet("s2", frozenset({"at-truck-loc2", "in-truck", "box-in-transit"}), 3.0),
    ]
    for s in states:
        assert checker.certified_bound(s) == MIN_COST


def test_safe_bound_is_min_of_hcert_and_learned():
    checker = _checker()
    s = SymbolicStateSet("s", frozenset({"at-truck-loc1"}), 0.0)
    # h_cert=1.0, learned=0.5 → safe=min(1.0, 0.5)=0.5
    assert checker.safe_bound(s, learned_estimate=0.5) == 0.5
    # h_cert=1.0, learned=5.0 → safe=min(1.0, 5.0)=1.0
    assert checker.safe_bound(s, learned_estimate=5.0) == 1.0


def test_pruning_allowed_when_gcost_plus_hcert_exceeds_incumbent():
    checker = _checker()
    # g=3.5, h_cert=1.0 → g+h=4.5 ≥ incumbent=4.0 → prune
    s = SymbolicStateSet("s", frozenset({"at-truck-loc2", "in-truck"}), 3.5)
    cert = checker.check_pruning_bound(s, incumbent_cost=4.0)
    assert cert.valid
    assert cert.metadata["h_cert"] == 1.0


def test_pruning_rejected_when_hcert_insufficient():
    checker = _checker()
    # g=1.0, h_cert=1.0 → g+h=2.0 < incumbent=4.0 → keep
    s = SymbolicStateSet("s", frozenset({"at-truck-loc1", "in-truck"}), 1.0)
    cert = checker.check_pruning_bound(s, incumbent_cost=4.0)
    assert not cert.valid


def test_hcert_zero_without_task_info():
    """Without set_task_info, h_cert must fall back to 0.0 (backward compat)."""
    checker = AdmissibleBoundChecker()
    s = SymbolicStateSet("s", frozenset({"at-truck-loc1"}), 0.0)
    assert checker.certified_bound(s) == 0.0


def test_safe_bound_without_learned_estimate():
    checker = _checker()
    s = SymbolicStateSet("s", frozenset({"at-truck-loc1"}), 0.0)
    assert checker.safe_bound(s) == MIN_COST
