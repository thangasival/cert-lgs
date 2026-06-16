# Cert-LGS: Certified Learning-Guided Symbolic Search

**Target paper:** Optimality-Preserving Learned Guidance for Symbolic Search over Expressive PDDL Models  
**Target journal:** Journal of Artificial Intelligence Research (JAIR)  
**Central claim:** Learning can safely accelerate expressive cost-optimal symbolic planning when learned decisions are restricted to proposal-only guidance and all correctness-relevant actions are verified by a symbolic certification layer.

This repository is a starter pipeline for the proposed JAIR research project. It is structured around one central contribution: **certified learned guidance for expressive symbolic search**.

## What this repository contains

```text
cert-lgs/
  README.md
  pyproject.toml
  requirements.txt
  environment.yml
  Makefile
  configs/
  src/cert_lgs/
    planner/
    learning/
    certification/
    utils/
  experiments/
  benchmarks/
  tests/
  paper/
  docs/
```

## Repository philosophy

The learned model is never trusted for correctness.

It may propose:

- operator priority,
- frontier expansion order,
- symbolic partition order,
- abstraction-refinement priority,
- BDD/representation hints.

But the symbolic certification layer must approve anything that affects:

- pruning,
- transition semantics,
- admissible lower bounds,
- dominance,
- partition coverage,
- plan acceptance,
- cost optimality.

## Quick start

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -e ".[dev]"
pytest
python -m cert_lgs.cli --config configs/default.yaml
```

## Run experiment scripts

```bash
python experiments/run_baselines.py --config configs/default.yaml
python experiments/run_cert_lgs.py --config configs/default.yaml
python experiments/run_ablations.py --config configs/default.yaml
python experiments/run_adversarial_tests.py --config configs/adversarial.yaml
python experiments/aggregate_results.py --results-dir results/raw
```

## Core certification theorem package

The implementation is designed to support these theorem claims:

1. **Soundness:** every returned plan is valid for the expressive planning task.
2. **Completeness:** for finite tasks, if a solution exists, certified fallback preserves completeness.
3. **Cost optimality:** learned guidance cannot cause cheaper plans to be pruned unless a certified admissible bound permits pruning.
4. **Learning robustness:** arbitrary learned-model errors can slow search but cannot invalidate correctness.
5. **Baseline degradation:** if all learned proposals are rejected, Cert-LGS reduces to the certified symbolic baseline up to proposal/certification overhead.

## Current status

This is a research scaffold, not a completed planner. The structure is designed so you can incrementally replace the placeholder symbolic backend with a real PDDL/symbolic-search engine.

## Minimum JAIR-level completion checklist

- [ ] Implement real expressive PDDL parser or integrate an existing parser.
- [ ] Implement symbolic state-set backend.
- [ ] Implement conditional-effect semantics.
- [ ] Implement derived-predicate/axiom closure.
- [ ] Implement state-dependent action cost semantics.
- [ ] Implement real transition equivalence checks.
- [ ] Implement exhaustive partition certificates.
- [ ] Implement certified admissible-bound wrapper.
- [ ] Implement safe pruning certificates.
- [ ] Run adversarial learned-guidance tests.
- [ ] Add benchmark domains with conditional effects, axioms, and state-dependent costs.
- [ ] Compare against expressive symbolic-search and learned-heuristic baselines.
- [ ] Produce certificate logs and reproducibility package.
