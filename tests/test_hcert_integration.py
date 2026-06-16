"""Integration tests: h_cert bound fires correctly inside CertificationLayer.safe_to_enqueue().

These tests verify the end-to-end path:
    set_task() → bound_checker.set_task_info() → safe_to_enqueue()
               → check_pruning_bound() → g + h_cert >= incumbent → prune
"""
from types import SimpleNamespace

import pytest

from cert_lgs.certification.certifier import CertificationLayer
from cert_lgs.planner.types import Action, SymbolicStateSet


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _certifier(theta: float = 0.75) -> CertificationLayer:
    return CertificationLayer({"certification": {"pruning_confidence_threshold": theta}})


def _task(goal_atoms: frozenset[str], min_cost: float = 1.0) -> SimpleNamespace:
    actions = [Action("a", frozenset(), frozenset(), frozenset(), cost=min_cost)]
    return SimpleNamespace(goal_atoms=goal_atoms, actions=actions)


GOAL = frozenset({"delivered"})
CLOSED: list[SymbolicStateSet] = []   # empty closed list — no dominance pruning


# ---------------------------------------------------------------------------
# Core pruning-fires tests
# ---------------------------------------------------------------------------

def test_pruning_fires_when_g_plus_hcert_equals_incumbent():
    cert = _certifier()
    cert.set_task(_task(GOAL, min_cost=1.0))
    # g=3.0, h_cert=1.0 → g+h=4.0 == incumbent=4.0 → prune (>=)
    candidate = SymbolicStateSet("s", frozenset({"at-truck"}), g_cost=3.0)
    assert not cert.safe_to_enqueue(candidate, CLOSED, incumbent_cost=4.0)


def test_pruning_fires_when_g_plus_hcert_exceeds_incumbent():
    cert = _certifier()
    cert.set_task(_task(GOAL, min_cost=1.0))
    # g=3.5, h_cert=1.0 → g+h=4.5 > incumbent=4.0 → prune
    candidate = SymbolicStateSet("s", frozenset({"at-truck"}), g_cost=3.5)
    assert not cert.safe_to_enqueue(candidate, CLOSED, incumbent_cost=4.0)


def test_pruning_suppressed_when_g_plus_hcert_below_incumbent():
    cert = _certifier()
    cert.set_task(_task(GOAL, min_cost=1.0))
    # g=1.0, h_cert=1.0 → g+h=2.0 < incumbent=4.0 → keep
    candidate = SymbolicStateSet("s", frozenset({"at-truck"}), g_cost=1.0)
    assert cert.safe_to_enqueue(candidate, CLOSED, incumbent_cost=4.0)


def test_pruning_suppressed_at_goal_state():
    cert = _certifier()
    cert.set_task(_task(GOAL, min_cost=1.0))
    # goal is satisfied → h_cert=0.0, g+h=3.0 < incumbent=4.0 → keep
    candidate = SymbolicStateSet("s", frozenset({"delivered"}), g_cost=3.0)
    assert cert.safe_to_enqueue(candidate, CLOSED, incumbent_cost=4.0)


# ---------------------------------------------------------------------------
# Backward-compatibility: h_cert=0.0 without set_task()
# ---------------------------------------------------------------------------

def test_no_pruning_without_task_injection():
    cert = _certifier()
    # Without set_task(), h_cert=0.0 → g+h=3.0 < incumbent=4.0 → keep
    candidate = SymbolicStateSet("s", frozenset({"at-truck"}), g_cost=3.0)
    assert cert.safe_to_enqueue(candidate, CLOSED, incumbent_cost=4.0)


def test_no_pruning_without_incumbent():
    cert = _certifier()
    cert.set_task(_task(GOAL))
    # incumbent=inf → bound check skipped entirely → keep
    candidate = SymbolicStateSet("s", frozenset({"at-truck"}), g_cost=99.0)
    assert cert.safe_to_enqueue(candidate, CLOSED, incumbent_cost=float("inf"))


# ---------------------------------------------------------------------------
# min_action_cost respected
# ---------------------------------------------------------------------------

def test_pruning_with_fractional_min_cost():
    cert = _certifier()
    cert.set_task(_task(GOAL, min_cost=0.5))
    # g=3.5, h_cert=0.5 → g+h=4.0 == incumbent=4.0 → prune
    candidate = SymbolicStateSet("s", frozenset({"at-truck"}), g_cost=3.5)
    assert not cert.safe_to_enqueue(candidate, CLOSED, incumbent_cost=4.0)


def test_pruning_suppressed_with_fractional_min_cost_and_low_g():
    cert = _certifier()
    cert.set_task(_task(GOAL, min_cost=0.5))
    # g=1.0, h_cert=0.5 → g+h=1.5 < incumbent=4.0 → keep
    candidate = SymbolicStateSet("s", frozenset({"at-truck"}), g_cost=1.0)
    assert cert.safe_to_enqueue(candidate, CLOSED, incumbent_cost=4.0)


# ---------------------------------------------------------------------------
# Certificate count increments correctly
# ---------------------------------------------------------------------------

def test_safe_to_enqueue_increments_checked_count():
    cert = _certifier()
    cert.set_task(_task(GOAL))
    candidate = SymbolicStateSet("s", frozenset({"at-truck"}), g_cost=3.0)
    before = cert.checked
    cert.safe_to_enqueue(candidate, CLOSED, incumbent_cost=4.0)
    # dominance_pruning cert + admissible_bound_pruning cert → +2
    assert cert.checked >= before + 1
