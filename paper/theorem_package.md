# Theorem Package Draft

## Definition: Safe Learned Proposal

A learned proposal is safe if accepting it either only changes the order of future certified symbolic expansions or is accompanied by a valid symbolic certificate proving semantic preservation, exhaustive coverage, admissibility, dominance, or safe pruning.

## Theorem 1: Soundness

If Cert-LGS returns a plan, then the plan is valid for the expressive planning task.

## Theorem 2: Completeness

For finite expressive planning tasks, if a solution exists, Cert-LGS eventually finds a solution.

## Theorem 3: Cost Optimality

For nonnegative state-dependent action costs, if Cert-LGS returns a plan, then the plan is cost-optimal.

## Theorem 4: Robustness to Learned-Model Error

For any learned model, including an adversarially wrong model, Cert-LGS preserves soundness, completeness, and optimality.

## Theorem 5: Baseline Degradation

If the certification layer rejects all non-ordering learned proposals, Cert-LGS reduces to the baseline symbolic-search planner up to proposal-evaluation and certification overhead.
