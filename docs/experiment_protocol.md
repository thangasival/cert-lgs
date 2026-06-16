# Experiment Protocol

## Main research questions

RQ1. Does Cert-LGS improve runtime, coverage, and memory?

RQ2. Does Cert-LGS preserve verified optimality?

RQ3. Which learned proposal types help most?

RQ4. How often are learned proposals rejected by certification?

RQ5. What happens when learning is adversarially wrong?

## Metrics

- coverage,
- runtime,
- memory,
- BDD node count,
- expanded symbolic frontiers,
- plan cost,
- certificate acceptance rate,
- certificate rejection rate,
- fallback rate,
- calibration error.

## Mandatory ablations

- no learning,
- random guidance,
- no certifier,
- no admissible-bound certificate,
- no partition certificate,
- no transition certificate,
- adversarial learned model.
