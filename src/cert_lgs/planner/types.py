from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ConditionalEffect:
    """A PDDL conditional effect: when condition holds in pre-state, apply add/del."""
    condition: frozenset[str]
    add_atoms: frozenset[str]
    del_atoms: frozenset[str]


@dataclass(frozen=True)
class Action:
    """A grounded PDDL action."""
    name: str
    preconditions: frozenset[str]
    add_effects: frozenset[str]
    del_effects: frozenset[str]
    cost: float = 1.0
    conditional_effects: tuple[ConditionalEffect, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SymbolicStateSet:
    """Placeholder symbolic state-set abstraction."""

    name: str
    states: frozenset[str] = field(default_factory=frozenset)
    g_cost: float = 0.0


@dataclass(frozen=True)
class TransitionRelation:
    name: str
    action_schema: str
    cost: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanStep:
    action: str
    cost: float = 1.0


@dataclass
class Plan:
    steps: list[PlanStep]

    @property
    def cost(self) -> float:
        return sum(step.cost for step in self.steps)


@dataclass
class PlannerResult:
    status: str
    plan: Plan | None
    plan_cost: float | None
    expanded: int
    certificates_checked: int
    certificates_rejected: int
    diagnostics: dict[str, Any] = field(default_factory=dict)
