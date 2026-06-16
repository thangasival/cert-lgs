from cert_lgs.certification.pruning_checker import PruningChecker
from cert_lgs.planner.types import SymbolicStateSet


def test_dominance_detected():
    closed = [SymbolicStateSet("A", frozenset({"s1", "s2"}), g_cost=1.0)]
    candidate = SymbolicStateSet("B", frozenset({"s1"}), g_cost=2.0)
    cert = PruningChecker().check_dominance(candidate, closed)
    assert cert.valid


def test_dominance_not_detected_when_cost_worse_in_closed():
    closed = [SymbolicStateSet("A", frozenset({"s1", "s2"}), g_cost=5.0)]
    candidate = SymbolicStateSet("B", frozenset({"s1"}), g_cost=2.0)
    cert = PruningChecker().check_dominance(candidate, closed)
    assert not cert.valid
