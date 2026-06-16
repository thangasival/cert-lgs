# Certification Layer Design

The certification layer is the core novelty.

## Golden rule

The learned model may propose. The symbolic certifier decides.

## Certifiers

1. Transition semantics checker.
2. Exhaustive partition checker.
3. Admissible-bound checker.
4. Safe-pruning checker.
5. Plan validator.

## Unsafe operations

The following are forbidden without a certificate:

- learned pruning,
- learned dominance,
- learned lower-bound pruning,
- learned plan acceptance,
- learned semantic transformation,
- learned abstraction refinement.

## Failure behavior

If a certificate fails:

1. Reject proposal.
2. Fall back to baseline symbolic behavior.
3. Log certificate failure.
4. Continue search.

This is what makes the system robust to wrong learning.
