# Cert-LGS: Certified Learning-Guided Symbolic Search

Implementation accompanying the paper:

> **Optimality-Preserving Learned Guidance for Symbolic Search over Expressive PDDL Models**
> *Submitted to Journal of Artificial Intelligence Research (JAIR), 2026*

---

## What is Cert-LGS?

Cert-LGS is a framework for safely integrating learned guidance into
cost-optimal symbolic planning over expressive PDDL models (conditional effects,
axioms, state-dependent action costs).

The core principle:

> *The learned model proposes. The certifier decides. The symbolic planner remains responsible for correctness.*

A GNN-based ranker proposes operator orderings, frontier partition orderings, and
pruning candidates. A four-certifier symbolic layer (C1–C4) verifies every
correctness-relevant proposal before execution. Proposals that fail certification
fall back to the baseline symbolic planner — guaranteed, with no interruption to
the search.

**Correctness guarantees** (Theorems 1–5 in the paper):
- **Soundness** — every returned plan is valid for the expressive planning task
- **Completeness** — certified fallback preserves completeness over the finite state space
- **Cost optimality** — learned guidance cannot cause suboptimal pruning
- **Adversarial robustness** — correctness holds for any learned model, including adversarially wrong ones
- **Baseline degradation bound** — a fully rejected learned model reduces Cert-LGS to the baseline planner

---

## Current status

| Component | Status |
|---|---|
| PDDL parser (toy domain, ground actions) | Done |
| Expressive semantics (conditional effects, axioms, SDAC) | Done |
| BDD backend (`dd` library wrapper) | Done |
| Symbolic search loop (UCS with certified proposals) | Done |
| C1 — Semantic transition certificate | Done |
| C2 — Exhaustive partition certificate | Done |
| C3 — Admissible lower-bound certificate | Done |
| C4 — Safe pruning certificate | Done |
| Certification orchestrator + fallback protocol | Done |
| Three-tier proposal routing (Tier 1/2/3) | Done |
| GNN proposal ranker | Done |
| P_cert feasibility predictor | Done |
| Composite training loss (rank + calib + bdd + safety + cert-feas) | Done |
| Calibration (temperature scaling + ECE) | Done |
| AdversarialRanker (worst-case test harness) | Done |
| Toy expressive logistics benchmark | Done |
| Adversarial robustness pilot (4/4 unsafe proposals rejected) | **Confirmed** |
| Automated test suite | **90 tests, all passing** |
| PDDL parser extension for parameterised actions + axioms | Pending |
| Full-scale IPC benchmark evaluation | Pending |
| GNN training on real benchmark instances | Pending |

---

## Pilot results (toy domain)

On the toy expressive logistics domain (4 ground actions, 1 conditional effect,
state-dependent costs):

| Method | Plan cost | States expanded | Cert. checks | Rejections |
|---|---|---|---|---|
| Cert-LGS (HeuristicRanker) | **4.0** (optimal) | 4 | 11 | 3 |
| Cert-LGS (AdversarialRanker) | **4.0** (optimal) | 4 | 15 | 7 |

All 4 adversarial pruning proposals are intercepted and rejected by C3. No
incorrect plan is produced. The optimal plan is recovered in both cases.
See `results/raw/adversarial_guidance.json` for the full certificate event log.

---

## Installation

```bash
# Python 3.10+
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

For GNN training (optional):

```bash
pip install -e ".[dev,ml]"
```

Dependencies are pinned in `pyproject.toml`. The BDD backend requires
`dd>=0.5.6` (pure-Python CUDD wrapper).

---

## Quick start

```bash
# Run all 90 tests
pytest

# Run with coverage
pytest --cov=cert_lgs --cov-report=term-missing

# Run the toy-domain pilot (HeuristicRanker)
python -m cert_lgs.cli --config configs/default.yaml

# Run the adversarial pilot (AdversarialRanker)
python -m cert_lgs.cli --config configs/adversarial.yaml
```

---

## Experiment scripts

```bash
# Baseline planners (Sym-Expressive, Sym-OpPot, Sym-Random)
python experiments/run_baselines.py --config configs/default.yaml

# Full Cert-LGS runs
python experiments/run_cert_lgs.py --config configs/default.yaml

# Ablation sweeps (certifier ablations, theta sensitivity)
python experiments/run_ablations.py --config configs/default.yaml

# Adversarial and out-of-distribution tests
python experiments/run_adversarial_tests.py --config configs/adversarial.yaml

# Aggregate results into tables and figures
python experiments/aggregate_results.py --results-dir results/raw
```

---

## Architecture

```
Expressive PDDL task Π
        │
        ▼
Expressive symbolic transition system
(conditional effects + axioms + state-dependent costs)
        │
        ▼
Symbolic search frontier OPEN
        │
    ┌───┴──────────────────────────┐
    │                              │
    ▼                              ▼
Learning module L          Certification layer C
(GNN ranker,               (C1 transition semantics,
 P_cert predictor,          C2 partition coverage,
 calibration)               C3 admissible bound,
    │                       C4 safe pruning)
    └──────────► Certified proposal queue
                           │
                           ▼
              Sound / complete / optimal
              expressive symbolic search
                           │
                           ▼
                     Optimal plan π*
```

### Three-tier proposal routing

| Tier | Proposal type | Fallback rate | Basis |
|---|---|---|---|
| 1 | Operator / partition ordering | **0%** | Guaranteed — no certifier invoked |
| 2 | BDD partition coverage (C2) | To be measured | One BDD equivalence check |
| 2 | Admissible bound (C3) | **0%** | Guaranteed — min(h_L, h_cert) always admissible |
| 3 | Safe pruning (C4, above θ) | To be measured | Strict certificate; domain-dependent |

---

## Repository structure

```
cert-lgs/
├── pyproject.toml              # Package metadata and dependencies
├── requirements.txt
├── environment.yml
├── Makefile
├── configs/
│   ├── default.yaml            # Default config (seed 42)
│   └── adversarial.yaml        # Adversarial ranker config (seed 13)
├── src/cert_lgs/
│   ├── planner/
│   │   ├── types.py            # Core type definitions
│   │   ├── parser.py           # PDDL parser
│   │   ├── expressive_semantics.py  # CE, axiom, SDAC evaluators
│   │   ├── transition_system.py     # BDD/EVMDD transition builder
│   │   ├── symbolic_search.py       # Core symbolic search loop
│   │   └── bdd_backend.py           # dd library wrapper
│   ├── learning/
│   │   ├── features.py         # Structural + diagnostic feature extraction
│   │   ├── proposals.py        # Proposal types + three-tier routing
│   │   ├── model.py            # GNN ranker + AdversarialRanker
│   │   ├── predict.py          # Online proposal generation
│   │   └── calibrate.py        # Temperature scaling + ECE
│   ├── certification/
│   │   ├── certificates.py          # Certificate dataclass
│   │   ├── transition_checker.py    # C1 — semantic transition
│   │   ├── partition_checker.py     # C2 — exhaustive partition
│   │   ├── admissible_bound_checker.py  # C3 — admissible bound
│   │   ├── pruning_checker.py       # C4 — safe pruning
│   │   ├── certifier.py             # Orchestrator + fallback protocol
│   │   └── plan_validator.py        # Post-hoc plan validity
│   └── utils/
│       ├── config.py           # YAML config loader
│       └── logging.py          # Certificate event logger
├── tests/                      # 90 automated tests
│   ├── test_parser.py
│   ├── test_transition_system.py
│   ├── test_bdd_backend.py
│   ├── test_search.py
│   ├── test_transition_checker.py
│   ├── test_partition_checker.py
│   ├── test_admissible_bound_checker.py
│   ├── test_pruning_checker.py
│   ├── test_certifier_adversarial.py
│   ├── test_hcert.py
│   ├── test_gnn_ranker.py
│   ├── test_pcert.py
│   └── test_training_loss.py
├── experiments/
│   ├── run_baselines.py
│   ├── run_cert_lgs.py
│   ├── run_ablations.py
│   ├── run_adversarial_tests.py
│   └── aggregate_results.py
├── benchmarks/
│   └── toy_expressive/
│       ├── domain.pddl         # Toy expressive logistics domain
│       ├── problem.pddl
│       └── README.md
├── results/
│   ├── raw/
│   │   └── adversarial_guidance.json  # Pilot certificate event log
│   ├── tables/                 # Generated at experiment time
│   └── figures/                # Generated at experiment time
└── docs/
    ├── certification_layer_design.md
    ├── experiment_protocol.md
    └── novelty_positioning.md
```

---

## Pending before full paper submission

- [ ] Extend PDDL parser to handle parameterised actions and axioms/derived predicates (required to load IPC benchmark domains)
- [ ] Train GNN guidance model on small expressive benchmark instances
- [ ] Run full-scale evaluation: Cert-LGS vs. Sym-Expressive, Sym-OpPot, GNN-Heuristic, Cert-LGS-NoCert across IPC domain Groups 1–3
- [ ] Measure per-tier fallback rates and θ-sensitivity on real benchmarks
- [ ] Document hardware specs and runtime environment for all timed experiments
- [ ] Verify all returned plans with independent PDDL validator
- [ ] Add full benchmark domains to `benchmarks/` and publish dataset

---

## Citation

Paper under submission. Citation to be added on acceptance.

```bibtex
@article{CertLGS2026,
  title   = {Optimality-Preserving Learned Guidance for Symbolic Search
             over Expressive {PDDL} Models},
  author  = {[Authors TBD]},
  journal = {Journal of Artificial Intelligence Research},
  year    = {2026},
  note    = {Under submission}
}
```

---

## License

MIT — see `LICENSE`.
