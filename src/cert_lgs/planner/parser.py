from __future__ import annotations

import re
from pathlib import Path

from cert_lgs.planner.types import (
    Action,
    ConditionalEffect,
    SymbolicStateSet,
    TransitionRelation,
)


# ---------------------------------------------------------------------------
# S-expression tokeniser and parser
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    text = re.sub(r";[^\n]*", "", text)
    text = text.replace("(", " ( ").replace(")", " ) ")
    return text.split()


def _parse_sexp(tokens: list[str]) -> list | str:
    if not tokens:
        raise ValueError("Unexpected end of tokens")
    tok = tokens.pop(0)
    if tok == "(":
        items: list = []
        while tokens and tokens[0] != ")":
            items.append(_parse_sexp(tokens))
        if tokens:
            tokens.pop(0)  # consume ')'
        return items
    return tok


# ---------------------------------------------------------------------------
# PDDL interpretation helpers
# ---------------------------------------------------------------------------

def _atom_str(sexp) -> str:
    """Convert a ground predicate sexp like ['at-truck-loc1'] to its atom string."""
    if isinstance(sexp, str):
        return sexp
    if isinstance(sexp, list) and len(sexp) == 1:
        return str(sexp[0])
    raise ValueError(f"Cannot convert {sexp!r} to an atom string")


def _parse_conjunction_atoms(sexp) -> frozenset[str]:
    """Parse (and (p1) (p2) ...) or a single predicate into a set of atom strings."""
    if sexp is None:
        return frozenset()
    if isinstance(sexp, str):
        return frozenset({sexp})
    if not isinstance(sexp, list) or not sexp:
        return frozenset()
    if sexp[0] == "and":
        atoms: set[str] = set()
        for item in sexp[1:]:
            head = item[0] if isinstance(item, list) else item
            if head in ("not", "when", "increase", "="):
                continue
            atoms.add(_atom_str(item))
        return frozenset(atoms)
    # Single predicate
    if sexp[0] not in ("not", "when", "increase", "="):
        return frozenset({_atom_str(sexp)})
    return frozenset()


def _parse_effects(
    sexp,
) -> tuple[frozenset[str], frozenset[str], list[ConditionalEffect], float]:
    """Return (add_atoms, del_atoms, conditional_effects, cost)."""
    add_atoms: set[str] = set()
    del_atoms: set[str] = set()
    cond_effects: list[ConditionalEffect] = []
    cost = 1.0

    if sexp is None:
        return frozenset(), frozenset(), [], cost

    items: list = sexp[1:] if (isinstance(sexp, list) and sexp and sexp[0] == "and") else [sexp]

    for item in items:
        if not isinstance(item, list):
            add_atoms.add(str(item))
            continue
        head = item[0]
        if head == "not":
            del_atoms.add(_atom_str(item[1]))
        elif head == "when":
            cond = _parse_conjunction_atoms(item[1])
            ce_body = item[2]
            ce_add, ce_del, _, _ = _parse_effects(ce_body)
            cond_effects.append(
                ConditionalEffect(condition=cond, add_atoms=ce_add, del_atoms=ce_del)
            )
        elif head == "increase":
            try:
                cost = float(item[2])
            except (IndexError, ValueError):
                cost = 1.0
        elif head not in ("=",):
            add_atoms.add(_atom_str(item))

    return frozenset(add_atoms), frozenset(del_atoms), cond_effects, cost


def _parse_actions(domain_sexp: list) -> list[Action]:
    actions: list[Action] = []
    for item in domain_sexp:
        if not isinstance(item, list) or not item or item[0] != ":action":
            continue
        name = item[1]
        prec_sexp = None
        eff_sexp = None
        i = 2
        while i < len(item):
            if item[i] == ":precondition":
                prec_sexp = item[i + 1]
                i += 2
            elif item[i] == ":effect":
                eff_sexp = item[i + 1]
                i += 2
            else:
                i += 1

        preconditions = _parse_conjunction_atoms(prec_sexp)
        add_effects, del_effects, cond_effects, cost = _parse_effects(eff_sexp)
        actions.append(
            Action(
                name=name,
                preconditions=preconditions,
                add_effects=add_effects,
                del_effects=del_effects,
                cost=cost,
                conditional_effects=tuple(cond_effects),
            )
        )
    return actions


def _parse_init(problem_sexp: list) -> frozenset[str]:
    for item in problem_sexp:
        if isinstance(item, list) and item and item[0] == ":init":
            atoms: set[str] = set()
            for atom in item[1:]:
                if isinstance(atom, list) and atom[0] not in ("=", "increase"):
                    try:
                        atoms.add(_atom_str(atom))
                    except ValueError:
                        pass
            return frozenset(atoms)
    return frozenset()


def _parse_goal(problem_sexp: list) -> frozenset[str]:
    for item in problem_sexp:
        if isinstance(item, list) and item and item[0] == ":goal":
            return _parse_conjunction_atoms(item[1])
    return frozenset()


# ---------------------------------------------------------------------------
# Public PlanningTask
# ---------------------------------------------------------------------------

class PlanningTask:
    def __init__(
        self,
        name: str,
        initial: SymbolicStateSet,
        transitions: list[TransitionRelation],
        initial_atoms: frozenset[str],
        goal_atoms: frozenset[str],
        actions: list[Action],
    ):
        self.name = name
        self.initial = initial
        self.transitions = transitions  # kept for backward-compat with guide.propose()
        self.initial_atoms = initial_atoms
        self.goal_atoms = goal_atoms
        self.actions = actions


def parse_task(domain_dir: Path) -> PlanningTask:
    """Parse domain.pddl + problem.pddl from *domain_dir* into a PlanningTask.

    Falls back to a hard-coded toy task if the files are missing or empty.
    """
    domain_file = domain_dir / "domain.pddl"
    problem_file = domain_dir / "problem.pddl"

    if domain_file.exists() and problem_file.exists():
        domain_text = domain_file.read_text(encoding="utf-8")
        problem_text = problem_file.read_text(encoding="utf-8")

        domain_tokens = _tokenize(domain_text)
        problem_tokens = _tokenize(problem_text)

        if domain_tokens and problem_tokens:
            domain_sexp = _parse_sexp(domain_tokens)
            problem_sexp = _parse_sexp(problem_tokens)

            actions = _parse_actions(domain_sexp)
            init_atoms = _parse_init(problem_sexp)
            goal_atoms = _parse_goal(problem_sexp)

            if actions and goal_atoms:
                initial_sss = SymbolicStateSet(name="I", states=init_atoms, g_cost=0.0)
                transitions = [
                    TransitionRelation(name=a.name, action_schema=a.name, cost=a.cost)
                    for a in actions
                ]
                return PlanningTask(
                    name=domain_dir.name,
                    initial=initial_sss,
                    transitions=transitions,
                    initial_atoms=init_atoms,
                    goal_atoms=goal_atoms,
                    actions=actions,
                )

    # Fallback: hard-coded toy task matching the original stubs.
    return _fallback_task(domain_dir.name)


def _fallback_task(name: str) -> PlanningTask:
    initial = SymbolicStateSet(name="I", states=frozenset({"s0"}), g_cost=0.0)
    transitions = [
        TransitionRelation(name="load", action_schema="load(?x)", cost=1.0),
        TransitionRelation(name="move", action_schema="move(?from,?to)", cost=2.0),
        TransitionRelation(name="deliver", action_schema="deliver(?x)", cost=1.0),
    ]
    return PlanningTask(
        name=name,
        initial=initial,
        transitions=transitions,
        initial_atoms=frozenset({"s0"}),
        goal_atoms=frozenset(),
        actions=[],
    )
