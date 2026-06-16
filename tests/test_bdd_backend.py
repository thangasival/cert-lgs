from cert_lgs.planner.bdd_backend import BDDBackend


def test_dd_importable():
    b = BDDBackend()
    assert b.dd_available, "dd package must be installed"


def test_bdd_with_variables():
    b = BDDBackend(variables=["x", "y"])
    assert b.available


def test_bdd_equivalent_trivial():
    b = BDDBackend(variables=["x"])
    u = b.add_expr("x")
    v = b.add_expr("x")
    assert b.equivalent(u, v)


def test_bdd_not_equivalent():
    b = BDDBackend(variables=["x", "y"])
    u = b.add_expr("x")
    v = b.add_expr("y")
    assert not b.equivalent(u, v)


def test_bdd_is_false():
    b = BDDBackend(variables=["x"])
    false_node = b._manager.false
    assert b.is_false(false_node)


def test_frozenset_union_stub():
    """Stub union works on frozensets when no manager is initialised."""
    b = BDDBackend()  # no variables → manager is None
    a = frozenset({"s1", "s2"})
    c = frozenset({"s3"})
    result = b.union(a, c)
    assert result == frozenset({"s1", "s2", "s3"})
