from cert_lgs.planner.types import Action, ConditionalEffect
from cert_lgs.planner.transition_system import TransitionSystem


def _logistics_actions():
    return [
        Action(
            name="load-at-loc1",
            preconditions=frozenset({"at-truck-loc1"}),
            add_effects=frozenset({"in-truck"}),
            del_effects=frozenset(),
            cost=1.0,
        ),
        Action(
            name="move-loc1-to-loc2",
            preconditions=frozenset({"at-truck-loc1"}),
            add_effects=frozenset({"at-truck-loc2"}),
            del_effects=frozenset({"at-truck-loc1"}),
            cost=2.0,
            conditional_effects=(
                ConditionalEffect(
                    condition=frozenset({"in-truck"}),
                    add_atoms=frozenset({"box-in-transit"}),
                    del_atoms=frozenset(),
                ),
            ),
        ),
        Action(
            name="deliver-at-loc2",
            preconditions=frozenset({"at-truck-loc2", "in-truck"}),
            add_effects=frozenset({"delivered"}),
            del_effects=frozenset({"in-truck", "box-in-transit"}),
            cost=1.0,
        ),
    ]


def test_applicable_action():
    ts = TransitionSystem(_logistics_actions())
    atoms = frozenset({"at-truck-loc1"})
    succs = ts.successors(atoms)
    names = {name for name, _, _ in succs}
    assert "load-at-loc1" in names
    assert "move-loc1-to-loc2" in names
    assert "deliver-at-loc2" not in names  # precondition not met


def test_conditional_effect_fires():
    ts = TransitionSystem(_logistics_actions())
    atoms = frozenset({"at-truck-loc1", "in-truck"})
    succs = {name: succ for name, succ, _ in ts.successors(atoms)}
    move_succ = succs["move-loc1-to-loc2"]
    assert "box-in-transit" in move_succ  # CE fired


def test_conditional_effect_does_not_fire():
    ts = TransitionSystem(_logistics_actions())
    atoms = frozenset({"at-truck-loc1"})  # no in-truck
    succs = {name: succ for name, succ, _ in ts.successors(atoms)}
    move_succ = succs["move-loc1-to-loc2"]
    assert "box-in-transit" not in move_succ  # CE did not fire


def test_optimal_plan_cost():
    ts = TransitionSystem(_logistics_actions())
    # Simulate: load → move → deliver
    s0 = frozenset({"at-truck-loc1"})
    s1_atoms, c1 = ts.apply(s0, _logistics_actions()[0])  # load
    assert "in-truck" in s1_atoms
    s2_atoms, c2 = ts.apply(s1_atoms, _logistics_actions()[1])  # move
    assert "box-in-transit" in s2_atoms
    s3_atoms, c3 = ts.apply(s2_atoms, _logistics_actions()[2])  # deliver
    assert "delivered" in s3_atoms
    assert c1 + c2 + c3 == 4.0
