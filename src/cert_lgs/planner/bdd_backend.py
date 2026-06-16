from __future__ import annotations

try:
    import dd.autoref as _dd_autoref  # type: ignore[import-untyped]
    _DD_AVAILABLE = True
except ImportError:
    _dd_autoref = None  # type: ignore[assignment]
    _DD_AVAILABLE = False


class BDDBackend:
    """BDD symbolic-representation backend.

    Uses the `dd` library (https://github.com/tulip-control/dd) when available.
    Falls back to Python-object equality stubs otherwise so that the rest of
    the pipeline can import and run without a BDD installation.
    """

    def __init__(self, variables: list[str] | None = None):
        self._manager = None
        if _DD_AVAILABLE and variables:
            self._manager = _dd_autoref.BDD()
            for v in variables:
                self._manager.declare(v)

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    @property
    def available(self) -> bool:
        return _DD_AVAILABLE and self._manager is not None

    @property
    def dd_available(self) -> bool:
        """True if the `dd` package is importable (regardless of manager state)."""
        return _DD_AVAILABLE

    # ------------------------------------------------------------------
    # Manager helpers
    # ------------------------------------------------------------------

    def declare(self, *variables: str) -> None:
        if self.available:
            for v in variables:
                if v not in self._manager.vars:
                    self._manager.declare(v)

    def add_expr(self, expression: str):
        """Create a BDD node from a Boolean expression string (e.g. 'x & ~y')."""
        if self.available:
            return self._manager.add_expr(expression)
        return expression  # stub: return the string itself

    # ------------------------------------------------------------------
    # Core BDD operations
    # ------------------------------------------------------------------

    def node_count(self, bdd_node) -> int:
        """Number of BDD nodes in *bdd_node*'s DAG."""
        if self.available:
            try:
                return self._manager.count(bdd_node, nvars=len(self._manager.vars))
            except Exception:
                pass
        return len(str(bdd_node))

    def equivalent(self, left, right) -> bool:
        """True iff *left* and *right* represent the same Boolean function."""
        if self.available:
            return left == right  # dd uses structural equality for reduced OBDDs
        return left == right

    def union(self, left, right):
        """Disjunction (set union) of two BDD nodes."""
        if self.available:
            return self._manager.apply("or", left, right)
        # Stub: union of frozensets
        if isinstance(left, frozenset) and isinstance(right, frozenset):
            return left | right
        return left

    def intersection(self, left, right):
        """Conjunction (set intersection) of two BDD nodes."""
        if self.available:
            return self._manager.apply("and", left, right)
        if isinstance(left, frozenset) and isinstance(right, frozenset):
            return left & right
        return left

    def is_false(self, bdd_node) -> bool:
        """True iff the BDD node represents the empty set (False function)."""
        if self.available:
            return bdd_node == self._manager.false
        if isinstance(bdd_node, frozenset):
            return len(bdd_node) == 0
        return not bool(bdd_node)
