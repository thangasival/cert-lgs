from cert_lgs.certification.admissible_bound_checker import AdmissibleBoundChecker
from cert_lgs.planner.types import SymbolicStateSet


def test_safe_bound_never_exceeds_zero_placeholder():
    checker = AdmissibleBoundChecker()
    state = SymbolicStateSet("S", frozenset({"s"}), g_cost=1.0)
    assert checker.safe_bound(state, learned_estimate=100.0) == 0.0


def test_pruning_bound_rejects_when_incumbent_infinite():
    checker = AdmissibleBoundChecker()
    state = SymbolicStateSet("S", frozenset({"s"}), g_cost=1.0)
    cert = checker.check_pruning_bound(state, incumbent_cost=float("inf"))
    assert not cert.valid
