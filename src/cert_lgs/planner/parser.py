from __future__ import annotations

import re
from pathlib import Path

from cert_lgs.planner.types import (
    Action,
    AxiomRule,
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
            tokens.pop(0)
        return items
    return tok


# ---------------------------------------------------------------------------
# Atom-string helpers
# ---------------------------------------------------------------------------

def _ground_atom(pred: str, args: list[str]) -> str:
    """Return the canonical ground-atom string for predicate + argument list."""
    if args:
        return pred + " " + " ".join(args)
    return pred


def _atom_str(sexp) -> str:
    """Convert a ground-predicate sexp to its atom string (no-arg or multi-arg)."""
    if isinstance(sexp, str):
        return sexp
    if isinstance(sexp, list):
        if len(sexp) == 1:
            return str(sexp[0])
        return _ground_atom(str(sexp[0]), [str(a) for a in sexp[1:]])
    raise ValueError(f"Cannot convert {sexp!r} to an atom string")


# ---------------------------------------------------------------------------
# Type-system helpers
# ---------------------------------------------------------------------------

def _parse_typed_list(tokens_or_sexp: list) -> dict[str, str]:
    """Parse a typed list like [?x - type1 ?y - type2 obj1 obj2 - type3].

    Returns {name: type}.  Untyped names get type 'object'.
    """
    result: dict[str, str] = {}
    items = list(tokens_or_sexp)
    i = 0
    pending: list[str] = []
    while i < len(items):
        tok = items[i]
        if tok == "-":
            # Next token is the type for all names in `pending`
            if i + 1 < len(items):
                type_name = str(items[i + 1]).lower()
                for name in pending:
                    result[name] = type_name
                pending = []
                i += 2
            else:
                i += 1
        else:
            pending.append(str(tok).lower())
            i += 1
    # Remaining names without explicit type get 'object'
    for name in pending:
        result[name] = "object"
    return result


def _parse_types_section(domain_sexp: list) -> dict[str, str]:
    """Parse :types section → {child_type: parent_type}."""
    for item in domain_sexp:
        if isinstance(item, list) and item and item[0] == ":types":
            return _parse_typed_list(item[1:])
    return {}


def _parse_constants(domain_sexp: list) -> dict[str, str]:
    """Parse :constants section → {const_name: type}."""
    for item in domain_sexp:
        if isinstance(item, list) and item and item[0] == ":constants":
            return _parse_typed_list(item[1:])
    return {}


def _parse_objects(problem_sexp: list) -> dict[str, str]:
    """Parse :objects section → {obj_name: type}."""
    for item in problem_sexp:
        if isinstance(item, list) and item and item[0] == ":objects":
            return _parse_typed_list(item[1:])
    return {}


def _objects_by_type(
    obj_map: dict[str, str],
    type_hierarchy: dict[str, str],
) -> dict[str, list[str]]:
    """Index objects by their type (including supertypes via hierarchy)."""
    by_type: dict[str, list[str]] = {}
    for obj, obj_type in obj_map.items():
        # Walk the type chain upward and register under every ancestor.
        current = obj_type
        visited: set[str] = set()
        while current and current not in visited:
            by_type.setdefault(current, []).append(obj)
            visited.add(current)
            current = type_hierarchy.get(current)
        # Always register under 'object'
        by_type.setdefault("object", []).append(obj)
    return by_type


# ---------------------------------------------------------------------------
# Precondition / effect parsing  (with optional variable→object substitution)
# ---------------------------------------------------------------------------

def _substitute(sexp, binding: dict[str, str]):
    """Recursively replace variable strings in sexp using binding."""
    if isinstance(sexp, str):
        return binding.get(sexp, sexp)
    return [_substitute(item, binding) for item in sexp]


def _parse_conjunction_atoms(sexp, binding: dict[str, str] | None = None) -> frozenset[str]:
    """Parse (and (p1 a b) (p2 c) ...) or a single predicate into ground atom strings."""
    if binding:
        sexp = _substitute(sexp, binding)
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
    binding: dict[str, str] | None = None,
) -> tuple[frozenset[str], frozenset[str], list[ConditionalEffect], float]:
    """Return (add_atoms, del_atoms, conditional_effects, cost)."""
    if binding:
        sexp = _substitute(sexp, binding)

    add_atoms: set[str] = set()
    del_atoms: set[str] = set()
    cond_effects: list[ConditionalEffect] = []
    cost = 1.0

    if sexp is None:
        return frozenset(), frozenset(), [], cost

    items = sexp[1:] if (isinstance(sexp, list) and sexp and sexp[0] == "and") else [sexp]

    for item in items:
        if not isinstance(item, list):
            add_atoms.add(str(item))
            continue
        head = item[0]
        if head == "not":
            del_atoms.add(_atom_str(item[1]))
        elif head == "when":
            cond = _parse_conjunction_atoms(item[1])
            ce_add, ce_del, _, _ = _parse_effects(item[2])
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


# ---------------------------------------------------------------------------
# Ground-action parser  (no parameters → used for the toy domain)
# ---------------------------------------------------------------------------

def _parse_ground_actions(domain_sexp: list) -> list[Action]:
    """Parse actions with empty :parameters () or missing :parameters."""
    actions: list[Action] = []
    for item in domain_sexp:
        if not isinstance(item, list) or not item or item[0] != ":action":
            continue
        name = item[1]
        prec_sexp = None
        eff_sexp = None
        i = 2
        while i < len(item):
            if item[i] == ":parameters":
                i += 2  # skip (  ) block
            elif item[i] == ":precondition":
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


# ---------------------------------------------------------------------------
# Parameterised-action parser + grounder
# ---------------------------------------------------------------------------

def _parse_action_schema(item: list) -> tuple[str, list[str], dict[str, str], object, object]:
    """Extract (action_name, param_names, param_types, prec_sexp, eff_sexp) from an action item."""
    name = item[1]
    param_names: list[str] = []
    param_types: dict[str, str] = {}
    prec_sexp = None
    eff_sexp = None
    i = 2
    while i < len(item):
        if item[i] == ":parameters":
            raw_params = item[i + 1]  # sexp list like ['?x', '-', 'type', '?y', '-', 'type']
            typed = _parse_typed_list(raw_params)
            param_names = list(typed.keys())
            param_types = typed
            i += 2
        elif item[i] == ":precondition":
            prec_sexp = item[i + 1]
            i += 2
        elif item[i] == ":effect":
            eff_sexp = item[i + 1]
            i += 2
        else:
            i += 1
    return name, param_names, param_types, prec_sexp, eff_sexp


def _enumerate_bindings(
    param_names: list[str],
    param_types: dict[str, str],
    by_type: dict[str, list[str]],
) -> list[dict[str, str]]:
    """Return all variable→object bindings for a parameterised action."""
    if not param_names:
        return [{}]
    bindings: list[dict[str, str]] = [{}]
    for param in param_names:
        ptype = param_types.get(param, "object")
        candidates = by_type.get(ptype, [])
        new_bindings: list[dict[str, str]] = []
        for binding in bindings:
            for obj in candidates:
                new_bindings.append({**binding, param: obj})
        bindings = new_bindings
    return bindings


def _ground_actions(
    domain_sexp: list,
    by_type: dict[str, list[str]],
) -> list[Action]:
    """Ground all parameterised actions in the domain."""
    actions: list[Action] = []
    for item in domain_sexp:
        if not isinstance(item, list) or not item or item[0] != ":action":
            continue
        schema_name, param_names, param_types, prec_sexp, eff_sexp = _parse_action_schema(item)

        # No parameters → treat as ground action
        if not param_names:
            preconditions = _parse_conjunction_atoms(prec_sexp)
            add_effects, del_effects, cond_effects, cost = _parse_effects(eff_sexp)
            actions.append(
                Action(
                    name=schema_name,
                    preconditions=preconditions,
                    add_effects=add_effects,
                    del_effects=del_effects,
                    cost=cost,
                    conditional_effects=tuple(cond_effects),
                )
            )
            continue

        # Ground each valid binding
        bindings = _enumerate_bindings(param_names, param_types, by_type)
        for binding in bindings:
            # Ground action name: schema_name-obj1-obj2-...
            arg_suffix = "-".join(binding[p] for p in param_names)
            ground_name = f"{schema_name}-{arg_suffix}" if arg_suffix else schema_name

            preconditions = _parse_conjunction_atoms(prec_sexp, binding)
            add_effects, del_effects, cond_effects, cost = _parse_effects(eff_sexp, binding)
            actions.append(
                Action(
                    name=ground_name,
                    preconditions=preconditions,
                    add_effects=add_effects,
                    del_effects=del_effects,
                    cost=cost,
                    conditional_effects=tuple(cond_effects),
                )
            )
    return actions


# ---------------------------------------------------------------------------
# Axiom / derived-predicate parsing
# ---------------------------------------------------------------------------

def _parse_axioms(domain_sexp: list, by_type: dict[str, list[str]]) -> list[AxiomRule]:
    """Parse :derived rules and ground them into AxiomRule objects."""
    rules: list[AxiomRule] = []
    for item in domain_sexp:
        if not isinstance(item, list) or not item or item[0] != ":derived":
            continue
        # (:derived (derived-pred ?args) (body))
        head_sexp = item[1]
        body_sexp = item[2] if len(item) > 2 else None

        if not isinstance(head_sexp, list) or not head_sexp:
            continue

        pred_name = str(head_sexp[0])
        # Collect parameters from head (may be typed or untyped)
        raw_params = head_sexp[1:]
        if not raw_params:
            # Ground derived predicate, no parameters
            body_atoms = _parse_conjunction_atoms(body_sexp)
            rules.append(AxiomRule(
                head=pred_name,
                head_args=(),
                body=body_atoms,
            ))
            continue

        # Detect if params are typed: look for '-' in raw_params
        if "-" in raw_params:
            param_types = _parse_typed_list(raw_params)
        else:
            param_types = {str(p): "object" for p in raw_params}
        param_names = list(param_types.keys())

        bindings = _enumerate_bindings(param_names, param_types, by_type)
        for binding in bindings:
            ground_head = _ground_atom(pred_name, [binding[p] for p in param_names])
            body_atoms = _parse_conjunction_atoms(body_sexp, binding)
            rules.append(AxiomRule(
                head=ground_head,
                head_args=tuple(binding[p] for p in param_names),
                body=body_atoms,
            ))
    return rules


# ---------------------------------------------------------------------------
# Init / goal parsers
# ---------------------------------------------------------------------------

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
# Helper: does the domain contain parameterised actions?
# ---------------------------------------------------------------------------

def _has_parameters(domain_sexp: list) -> bool:
    for item in domain_sexp:
        if not isinstance(item, list) or not item or item[0] != ":action":
            continue
        i = 2
        while i < len(item):
            if item[i] == ":parameters":
                params = item[i + 1]
                # Non-empty parameter list
                if isinstance(params, list) and params:
                    return True
                i += 2
            else:
                i += 1
    return False


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
        axiom_rules: list[AxiomRule] | None = None,
        objects: dict[str, str] | None = None,
    ):
        self.name = name
        self.initial = initial
        self.transitions = transitions
        self.initial_atoms = initial_atoms
        self.goal_atoms = goal_atoms
        self.actions = actions
        self.axiom_rules: list[AxiomRule] = axiom_rules or []
        self.objects: dict[str, str] = objects or {}


def parse_task(domain_dir: Path) -> PlanningTask:
    """Parse domain.pddl + problem.pddl from *domain_dir* into a PlanningTask.

    Supports:
      - Ground PDDL (toy domain, no parameters)
      - Parameterised PDDL with :types and :objects
      - Derived predicates / axioms (:derived)
      - Conditional effects
      - State-dependent action costs (:action-costs)

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

            # Type system
            type_hierarchy = _parse_types_section(domain_sexp)
            constants = _parse_constants(domain_sexp)
            objects_map = {**constants, **_parse_objects(problem_sexp)}
            by_type = _objects_by_type(objects_map, type_hierarchy)

            # Ground actions
            if _has_parameters(domain_sexp):
                actions = _ground_actions(domain_sexp, by_type)
            else:
                actions = _parse_ground_actions(domain_sexp)

            # Axiom rules
            axiom_rules = _parse_axioms(domain_sexp, by_type)

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
                    axiom_rules=axiom_rules,
                    objects=objects_map,
                )

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
