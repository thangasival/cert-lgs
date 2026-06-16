# Paper Outline

## Title

Optimality-Preserving Learned Guidance for Symbolic Search over Expressive PDDL Models

## Central Claim

Learning can safely accelerate expressive cost-optimal symbolic planning when learned decisions are restricted to proposal-only guidance and all correctness-relevant actions are verified by a symbolic certification layer.

## 1. Introduction

- Expressive PDDL models are compact but hard to solve optimally.
- Symbolic search preserves guarantees but can be expensive.
- Learned guidance improves efficiency but can be unsafe.
- Cert-LGS bridges this gap.

## 2. Related Work

- Expressive symbolic planning.
- Symbolic search and operator-potential heuristics.
- Learned planning heuristics.
- Admissibility-aware learning.
- LLM/PDDL adjacent work.

## 3. Problem Formulation

Define expressive cost-optimal planning with conditional effects, axioms / derived predicates, and state-dependent action costs.

## 4. Cert-LGS Framework

- Symbolic-search backbone.
- Learned proposal model.
- Certification layer.
- Safe fallback.

## 5. Theoretical Guarantees

- Soundness.
- Completeness.
- Cost optimality.
- Robustness to wrong learned guidance.
- Degradation to baseline.

## 6. Learning Methodology

- Features.
- Ranking labels.
- Calibration.
- Safety-aware loss.

## 7. Experimental Design

- Baselines.
- Expressive benchmarks.
- Metrics.
- Ablations.

## 8. Results

- Efficiency.
- Correctness.
- Certification diagnostics.
- Generalization.
- Failure modes.

## 9. Discussion

## 10. Limitations

## 11. Conclusion
