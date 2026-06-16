"""Tests for the extended PDDL parser: types, objects, parameterised actions, axioms."""

from __future__ import annotations

from pathlib import Path

import pytest

from cert_lgs.planner.parser import (
    _enumerate_bindings,
    _ground_actions,
    _parse_axioms,
    _parse_conjunction_atoms,
    _parse_effects,
    _parse_objects,
    _parse_sexp,
    _parse_typed_list,
    _parse_types_section,
    _tokenize,
    parse_task,
)
from cert_lgs.planner.types import AxiomRule


# ---------------------------------------------------------------------------
# Typed-list parser
# ---------------------------------------------------------------------------

def test_typed_list_simple():
    tokens = ["?x", "-", "type1", "?y", "-", "type2"]
    result = _parse_typed_list(tokens)
    assert result == {"?x": "type1", "?y": "type2"}


def test_typed_list_multiple_per_type():
    tokens = ["a", "b", "c", "-", "mytype"]
    result = _parse_typed_list(tokens)
    assert result == {"a": "mytype", "b": "mytype", "c": "mytype"}


def test_typed_list_untyped_defaults_to_object():
    tokens = ["x", "y"]
    result = _parse_typed_list(tokens)
    assert result == {"x": "object", "y": "object"}


def test_typed_list_mixed():
    tokens = ["a", "-", "t1", "b", "c"]
    result = _parse_typed_list(tokens)
    assert result["a"] == "t1"
    assert result["b"] == "object"
    assert result["c"] == "object"


# ---------------------------------------------------------------------------
# Type-section parsing (from a domain sexp)
# ---------------------------------------------------------------------------

def _domain_sexp_with_types():
    raw = """
    (define (domain test)
      (:types truck airplane - vehicle vehicle - object)
    )
    """
    tokens = _tokenize(raw)
    return _parse_sexp(tokens)


def test_parse_types_section():
    sexp = _domain_sexp_with_types()
    types = _parse_types_section(sexp)
    assert types.get("truck") == "vehicle"
    assert types.get("airplane") == "vehicle"
    assert types.get("vehicle") == "object"


# ---------------------------------------------------------------------------
# Binding enumeration
# ---------------------------------------------------------------------------

def test_enumerate_bindings_single_param():
    bindings = _enumerate_bindings(
        param_names=["?x"],
        param_types={"?x": "truck"},
        by_type={"truck": ["t1", "t2"]},
    )
    assert len(bindings) == 2
    assert {"?x": "t1"} in bindings
    assert {"?x": "t2"} in bindings


def test_enumerate_bindings_two_params():
    bindings = _enumerate_bindings(
        param_names=["?x", "?y"],
        param_types={"?x": "a", "?y": "b"},
        by_type={"a": ["a1", "a2"], "b": ["b1"]},
    )
    assert len(bindings) == 2
    assert all("?x" in b and "?y" in b for b in bindings)


def test_enumerate_bindings_empty_type_gives_no_bindings():
    bindings = _enumerate_bindings(
        param_names=["?x"],
        param_types={"?x": "truck"},
        by_type={"truck": []},
    )
    assert bindings == []


def test_enumerate_bindings_no_params():
    bindings = _enumerate_bindings([], {}, {})
    assert bindings == [{}]


# ---------------------------------------------------------------------------
# Grounding actions from sexp
# ---------------------------------------------------------------------------

def _simple_parameterised_domain_sexp():
    raw = """
    (define (domain simple)
      (:action move
        :parameters (?from - loc ?to - loc)
        :precondition (at ?from)
        :effect (and (at ?to) (not (at ?from)) (increase (total-cost) 1)))
    )
    """
    tokens = _tokenize(raw)
    return _parse_sexp(tokens)


def test_ground_actions_produces_all_pairs():
    domain = _simple_parameterised_domain_sexp()
    # Object names in by_type are used as-is; use lowercase to match atom strings.
    by_type = {"loc": ["a", "b", "c"]}
    actions = _ground_actions(domain, by_type)
    # 3 locs × 3 locs = 9 groundings
    assert len(actions) == 9
    names = {a.name for a in actions}
    assert "move-a-b" in names
    assert "move-b-a" in names


def test_ground_action_preconditions_substituted():
    domain = _simple_parameterised_domain_sexp()
    by_type = {"loc": ["x"]}
    actions = _ground_actions(domain, by_type)
    assert len(actions) == 1
    a = actions[0]
    assert "at x" in a.preconditions


def test_ground_action_add_effects_substituted():
    domain = _simple_parameterised_domain_sexp()
    by_type = {"loc": ["x"]}
    actions = _ground_actions(domain, by_type)
    a = actions[0]
    assert "at x" in a.add_effects


def test_ground_action_del_effects_substituted():
    domain = _simple_parameterised_domain_sexp()
    by_type = {"loc": ["x"]}
    actions = _ground_actions(domain, by_type)
    a = actions[0]
    assert "at x" in a.del_effects


def test_ground_action_cost():
    domain = _simple_parameterised_domain_sexp()
    by_type = {"loc": ["X"]}
    actions = _ground_actions(domain, by_type)
    assert actions[0].cost == 1.0


# ---------------------------------------------------------------------------
# Axiom / derived-predicate parsing
# ---------------------------------------------------------------------------

def _domain_with_derived():
    raw = """
    (define (domain axiom-test)
      (:derived (reachable ?x - node)
        (adjacent src ?x))
    )
    """
    tokens = _tokenize(raw)
    return _parse_sexp(tokens)


def test_parse_axioms_returns_rules():
    domain = _domain_with_derived()
    by_type = {"node": ["n1", "n2"]}
    rules = _parse_axioms(domain, by_type)
    assert len(rules) == 2
    assert all(isinstance(r, AxiomRule) for r in rules)


def test_parse_axiom_head_grounded():
    domain = _domain_with_derived()
    by_type = {"node": ["n1"]}
    rules = _parse_axioms(domain, by_type)
    assert rules[0].head == "reachable n1"


def test_parse_axiom_body_contains_grounded_atom():
    domain = _domain_with_derived()
    by_type = {"node": ["n1"]}
    rules = _parse_axioms(domain, by_type)
    # body: (adjacent src ?x) with ?x=n1 → "adjacent src n1"
    assert "adjacent src n1" in rules[0].body


# ---------------------------------------------------------------------------
# Integration: parse Group 1 benchmark (small problem)
# ---------------------------------------------------------------------------

LOGISTICS_DIR = Path("benchmarks/logistics_expressive")


@pytest.mark.skipif(
    not (LOGISTICS_DIR / "domain.pddl").exists(),
    reason="logistics_expressive benchmark not present",
)
def test_parse_logistics_p01_has_actions():
    import shutil, tempfile
    tmpdir = Path(tempfile.mkdtemp())
    try:
        shutil.copy(LOGISTICS_DIR / "domain.pddl", tmpdir / "domain.pddl")
        shutil.copy(LOGISTICS_DIR / "p01_small.pddl", tmpdir / "problem.pddl")
        task = parse_task(tmpdir)
        assert len(task.actions) > 0, "Expected grounded actions from logistics domain"
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.mark.skipif(
    not (LOGISTICS_DIR / "domain.pddl").exists(),
    reason="logistics_expressive benchmark not present",
)
def test_parse_logistics_p01_goal_nonempty():
    import shutil, tempfile
    tmpdir = Path(tempfile.mkdtemp())
    try:
        shutil.copy(LOGISTICS_DIR / "domain.pddl", tmpdir / "domain.pddl")
        shutil.copy(LOGISTICS_DIR / "p01_small.pddl", tmpdir / "problem.pddl")
        task = parse_task(tmpdir)
        assert len(task.goal_atoms) > 0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.mark.skipif(
    not (LOGISTICS_DIR / "domain.pddl").exists(),
    reason="logistics_expressive benchmark not present",
)
def test_parse_logistics_p02_low_fuel_in_init():
    import shutil, tempfile
    tmpdir = Path(tempfile.mkdtemp())
    try:
        shutil.copy(LOGISTICS_DIR / "domain.pddl", tmpdir / "domain.pddl")
        shutil.copy(LOGISTICS_DIR / "p02_small.pddl", tmpdir / "problem.pddl")
        task = parse_task(tmpdir)
        # low-fuel truck1 should appear in init
        assert any("low-fuel" in atom for atom in task.initial_atoms)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
