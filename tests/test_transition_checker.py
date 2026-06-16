from cert_lgs.certification.transition_checker import TransitionChecker
from cert_lgs.planner.types import Action, ConditionalEffect, SymbolicStateSet, TransitionRelation


def test_transition_rejects_negative_cost():
    source = SymbolicStateSet("S", frozenset({"s"}))
    transition = TransitionRelation("bad", "bad()", cost=-1.0)
    successor = SymbolicStateSet("S2", frozenset({"s2"}))
    cert = TransitionChecker().check(source, transition, successor)
    assert not cert.valid


def test_transition_accepts_nonempty_successor():
    """Without an Action, structural check only — backward-compatible."""
    source = SymbolicStateSet("S", frozenset({"s"}))
    transition = TransitionRelation("ok", "ok()", cost=1.0)
    successor = SymbolicStateSet("S2", frozenset({"s2"}))
    cert = TransitionChecker().check(source, transition, successor)
    assert cert.valid


def test_c1_accepts_correct_successor():
    """C1 accepts a successor that exactly matches PDDL add/del effects."""
    action = Action(
        name="load-at-loc1",
        preconditions=frozenset({"at-truck-loc1"}),
        add_effects=frozenset({"in-truck"}),
        del_effects=frozenset(),
        cost=1.0,
    )
    source = SymbolicStateSet("s0", frozenset({"at-truck-loc1"}), 0.0)
    transition = TransitionRelation("load-at-loc1", "load-at-loc1", 1.0)
    # Correct: pre-atoms unchanged plus in-truck added (no del effects)
    correct_succ = SymbolicStateSet("s1", frozenset({"at-truck-loc1", "in-truck"}), 1.0)
    cert = TransitionChecker().check(source, transition, correct_succ, action=action)
    assert cert.valid
    assert "placeholder" not in cert.reason


def test_c1_rejects_wrong_successor():
    """C1 rejects a successor with atoms that don't match PDDL semantics."""
    action = Action(
        name="load-at-loc1",
        preconditions=frozenset({"at-truck-loc1"}),
        add_effects=frozenset({"in-truck"}),
        del_effects=frozenset(),
        cost=1.0,
    )
    source = SymbolicStateSet("s0", frozenset({"at-truck-loc1"}), 0.0)
    transition = TransitionRelation("load-at-loc1", "load-at-loc1", 1.0)
    # Wrong: contains spurious atom instead of in-truck
    wrong_succ = SymbolicStateSet("s1", frozenset({"at-truck-loc1", "wrong-atom"}), 1.0)
    cert = TransitionChecker().check(source, transition, wrong_succ, action=action)
    assert not cert.valid
    assert "mismatch" in cert.reason
    assert "wrong-atom" in str(cert.metadata)


def test_c1_verifies_ce_fires():
    """C1 rejects a successor where the conditional effect should have fired but its
    resulting atom is absent — catching CE omission bugs."""
    action = Action(
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
    )
    source = SymbolicStateSet("s1", frozenset({"at-truck-loc1", "in-truck"}), 0.0)
    transition = TransitionRelation("move-loc1-to-loc2", "move-loc1-to-loc2", 2.0)

    # Missing box-in-transit: CE should fire (in-truck in pre-state) but is absent.
    wrong_succ = SymbolicStateSet("s2", frozenset({"at-truck-loc2", "in-truck"}), 2.0)
    cert = TransitionChecker().check(source, transition, wrong_succ, action=action)
    assert not cert.valid

    # Correct: CE fires, so box-in-transit must be present.
    correct_succ = SymbolicStateSet("s2", frozenset({"at-truck-loc2", "in-truck", "box-in-transit"}), 2.0)
    cert = TransitionChecker().check(source, transition, correct_succ, action=action)
    assert cert.valid


def test_c1_verifies_ce_does_not_fire():
    """C1 rejects a successor where box-in-transit appears even though the CE
    condition (in-truck) was absent from the pre-state."""
    action = Action(
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
    )
    source = SymbolicStateSet("s1", frozenset({"at-truck-loc1"}), 0.0)  # no in-truck
    transition = TransitionRelation("move-loc1-to-loc2", "move-loc1-to-loc2", 2.0)

    # CE must NOT fire: spuriously claiming box-in-transit is wrong.
    spurious_succ = SymbolicStateSet("s2", frozenset({"at-truck-loc2", "box-in-transit"}), 2.0)
    cert = TransitionChecker().check(source, transition, spurious_succ, action=action)
    assert not cert.valid

    # Correct: no box-in-transit.
    correct_succ = SymbolicStateSet("s2", frozenset({"at-truck-loc2"}), 2.0)
    cert = TransitionChecker().check(source, transition, correct_succ, action=action)
    assert cert.valid
