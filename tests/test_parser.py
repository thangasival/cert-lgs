from pathlib import Path

from cert_lgs.planner.parser import parse_task


DOMAIN_DIR = Path("benchmarks/toy_expressive")


def test_parse_task_loads_actions():
    task = parse_task(DOMAIN_DIR)
    assert len(task.actions) == 4
    names = {a.name for a in task.actions}
    assert "load-at-loc1" in names
    assert "move-loc1-to-loc2" in names
    assert "deliver-at-loc2" in names


def test_parse_task_initial_atoms():
    task = parse_task(DOMAIN_DIR)
    assert "at-truck-loc1" in task.initial_atoms


def test_parse_task_goal():
    task = parse_task(DOMAIN_DIR)
    assert task.goal_atoms == frozenset({"delivered"})


def test_parse_task_conditional_effect_present():
    task = parse_task(DOMAIN_DIR)
    move = next(a for a in task.actions if a.name == "move-loc1-to-loc2")
    assert len(move.conditional_effects) >= 1
    ce = move.conditional_effects[0]
    assert "in-truck" in ce.condition
    assert "box-in-transit" in ce.add_atoms


def test_parse_task_action_costs():
    task = parse_task(DOMAIN_DIR)
    load = next(a for a in task.actions if a.name == "load-at-loc1")
    move = next(a for a in task.actions if a.name == "move-loc1-to-loc2")
    deliver = next(a for a in task.actions if a.name == "deliver-at-loc2")
    assert load.cost == 1.0
    assert move.cost == 2.0
    assert deliver.cost == 1.0
