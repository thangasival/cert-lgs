"""Tests for least-fixed-point axiom closure in ExpressiveSemantics."""

from __future__ import annotations

import pytest

from cert_lgs.planner.expressive_semantics import ExpressiveFeatureFlags, ExpressiveSemantics
from cert_lgs.planner.types import AxiomRule


def _sem(rules: list[AxiomRule], axioms_enabled: bool = True) -> ExpressiveSemantics:
    flags = ExpressiveFeatureFlags(
        conditional_effects=True,
        axioms=axioms_enabled,
        state_dependent_costs=True,
    )
    sem = ExpressiveSemantics(flags, axiom_rules=rules)
    return sem


# ---------------------------------------------------------------------------
# Basic closure behaviour
# ---------------------------------------------------------------------------

def test_no_rules_returns_atoms_unchanged():
    sem = _sem([])
    atoms = frozenset({"a", "b"})
    assert sem.close_axioms(atoms) == atoms


def test_single_rule_fires():
    rule = AxiomRule(head="c", head_args=(), body=frozenset({"a", "b"}))
    sem = _sem([rule])
    result = sem.close_axioms(frozenset({"a", "b"}))
    assert "c" in result


def test_single_rule_does_not_fire_when_body_absent():
    rule = AxiomRule(head="c", head_args=(), body=frozenset({"a", "b"}))
    sem = _sem([rule])
    result = sem.close_axioms(frozenset({"a"}))
    assert "c" not in result


def test_original_atoms_preserved():
    rule = AxiomRule(head="c", head_args=(), body=frozenset({"a"}))
    sem = _sem([rule])
    result = sem.close_axioms(frozenset({"a"}))
    assert "a" in result
    assert "c" in result


# ---------------------------------------------------------------------------
# Chained / layered closure (multi-round fixed-point)
# ---------------------------------------------------------------------------

def test_two_layer_chain():
    # d0 ← {a}; d1 ← {d0}
    r0 = AxiomRule(head="d0", head_args=(), body=frozenset({"a"}))
    r1 = AxiomRule(head="d1", head_args=(), body=frozenset({"d0"}))
    sem = _sem([r0, r1])
    result = sem.close_axioms(frozenset({"a"}))
    assert "d0" in result
    assert "d1" in result


def test_three_layer_chain():
    rules = [
        AxiomRule(head="d0", head_args=(), body=frozenset({"base0", "base1"})),
        AxiomRule(head="d1", head_args=(), body=frozenset({"d0", "base2"})),
        AxiomRule(head="d2", head_args=(), body=frozenset({"d1", "base3"})),
    ]
    sem = _sem(rules)
    atoms = frozenset({"base0", "base1", "base2", "base3"})
    result = sem.close_axioms(atoms)
    assert "d0" in result
    assert "d1" in result
    assert "d2" in result


def test_chain_stops_at_missing_body_atom():
    rules = [
        AxiomRule(head="d0", head_args=(), body=frozenset({"a", "b"})),
        AxiomRule(head="d1", head_args=(), body=frozenset({"d0", "c"})),
    ]
    sem = _sem(rules)
    # c is missing → d1 should not fire
    result = sem.close_axioms(frozenset({"a", "b"}))
    assert "d0" in result
    assert "d1" not in result


# ---------------------------------------------------------------------------
# Head already present
# ---------------------------------------------------------------------------

def test_already_derived_head_is_idempotent():
    rule = AxiomRule(head="d0", head_args=(), body=frozenset({"a"}))
    sem = _sem([rule])
    # "d0" is already in the init set
    result = sem.close_axioms(frozenset({"a", "d0"}))
    assert "d0" in result
    # Check exactly one copy (frozenset — always unique)
    assert isinstance(result, frozenset)


# ---------------------------------------------------------------------------
# Disabled-axioms flag
# ---------------------------------------------------------------------------

def test_axioms_disabled_flag_skips_closure():
    rule = AxiomRule(head="d0", head_args=(), body=frozenset({"a"}))
    sem = _sem([rule], axioms_enabled=False)
    result = sem.close_axioms(frozenset({"a"}))
    assert "d0" not in result


# ---------------------------------------------------------------------------
# set_axiom_rules API
# ---------------------------------------------------------------------------

def test_set_axiom_rules_replaces_rules():
    sem = _sem([])
    rule = AxiomRule(head="d0", head_args=(), body=frozenset({"x"}))
    sem.set_axiom_rules([rule])
    result = sem.close_axioms(frozenset({"x"}))
    assert "d0" in result


def test_set_axiom_rules_empty_clears():
    rule = AxiomRule(head="d0", head_args=(), body=frozenset({"a"}))
    sem = _sem([rule])
    sem.set_axiom_rules([])
    result = sem.close_axioms(frozenset({"a"}))
    assert "d0" not in result


# ---------------------------------------------------------------------------
# Conditional effects helper
# ---------------------------------------------------------------------------

from cert_lgs.planner.types import ConditionalEffect


def test_conditional_effects_fires_when_condition_met():
    ce = ConditionalEffect(
        condition=frozenset({"cond"}),
        add_atoms=frozenset({"bonus"}),
        del_atoms=frozenset(),
    )
    sem = _sem([])
    state = frozenset({"cond"})
    add, delete = sem.evaluate_conditional_effects(state, [ce])
    assert "bonus" in add


def test_conditional_effects_does_not_fire_when_condition_absent():
    ce = ConditionalEffect(
        condition=frozenset({"cond"}),
        add_atoms=frozenset({"bonus"}),
        del_atoms=frozenset(),
    )
    sem = _sem([])
    state = frozenset({"other"})
    add, delete = sem.evaluate_conditional_effects(state, [ce])
    assert "bonus" not in add


def test_conditional_effects_disabled_flag():
    ce = ConditionalEffect(
        condition=frozenset({"cond"}),
        add_atoms=frozenset({"bonus"}),
        del_atoms=frozenset(),
    )
    flags = ExpressiveFeatureFlags(conditional_effects=False, axioms=True, state_dependent_costs=True)
    sem = ExpressiveSemantics(flags)
    add, delete = sem.evaluate_conditional_effects(frozenset({"cond"}), [ce])
    assert add == frozenset()


def test_conditional_effects_delete():
    ce = ConditionalEffect(
        condition=frozenset({"trigger"}),
        add_atoms=frozenset(),
        del_atoms=frozenset({"victim"}),
    )
    sem = _sem([])
    _, delete = sem.evaluate_conditional_effects(frozenset({"trigger"}), [ce])
    assert "victim" in delete


# ---------------------------------------------------------------------------
# State-dependent cost passthrough
# ---------------------------------------------------------------------------

def test_sdac_returns_base_cost():
    sem = _sem([])
    assert sem.state_dependent_cost(frozenset({"a"}), base_cost=3.5) == 3.5


def test_sdac_disabled_still_returns_base_cost():
    flags = ExpressiveFeatureFlags(conditional_effects=True, axioms=True, state_dependent_costs=False)
    sem = ExpressiveSemantics(flags)
    assert sem.state_dependent_cost(frozenset(), base_cost=2.0) == 2.0
