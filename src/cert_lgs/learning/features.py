from __future__ import annotations

from cert_lgs.planner.types import SymbolicStateSet, TransitionRelation


def frontier_features(state_set: SymbolicStateSet) -> dict[str, float]:
    return {
        "num_states": float(len(state_set.states)),
        "g_cost": float(state_set.g_cost),
        "name_length": float(len(state_set.name)),
    }


def transition_features(transition: TransitionRelation) -> dict[str, float]:
    return {
        "cost": float(transition.cost),
        "name_length": float(len(transition.name)),
    }
