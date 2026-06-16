# Novelty Positioning

Do not frame the paper as:

> We use ML to improve planning.

That is weak.

Frame it as:

> We introduce a certified learned-guidance interface for expressive symbolic cost-optimal planning, proving that learning cannot break soundness, completeness, or optimality.

## Central claim

Learning can safely accelerate expressive cost-optimal symbolic planning when learned decisions are restricted to proposal-only guidance and all correctness-relevant actions are verified by a symbolic certification layer.

## What is new

- Certification-aware learned guidance.
- Expressive planning target.
- Symbolic state-set search.
- Robustness to adversarial learned guidance.
- Fallback to baseline if learning fails.
