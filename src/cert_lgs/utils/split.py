"""Training / validation / test split utilities for Cert-LGS experiments.

All splits are deterministic given a seed so experiments are reproducible.
The split fractions are read from the loaded config or fall back to
(train=0.70, val=0.15, test=0.15).

Reproducibility contract
------------------------
* Random state is seeded from ``config["project"]["seed"]`` (default 42).
* The same seed always produces the same partition of problem files.
* Test-split files MUST NOT be used for model selection or threshold tuning.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")


def split_instances(
    instances: list[T],
    train: float = 0.70,
    val: float = 0.15,
    test: float = 0.15,
    seed: int = 42,
) -> tuple[list[T], list[T], list[T]]:
    """Randomly partition *instances* into (train, val, test) lists.

    Parameters
    ----------
    instances:
        Ordered list of items to split (e.g. file paths or task objects).
    train, val, test:
        Fractional sizes; must sum to 1.0 within floating-point tolerance.
    seed:
        RNG seed for reproducible shuffling.

    Returns
    -------
    (train_list, val_list, test_list)
    """
    if abs(train + val + test - 1.0) > 1e-6:
        raise ValueError(f"Split fractions must sum to 1.0; got {train + val + test}")

    shuffled = list(instances)
    rng = random.Random(seed)
    rng.shuffle(shuffled)

    n = len(shuffled)
    n_train = int(n * train)
    n_val   = int(n * val)
    return (
        shuffled[:n_train],
        shuffled[n_train : n_train + n_val],
        shuffled[n_train + n_val :],
    )


def collect_problem_files(domain_dirs: list[str | Path]) -> list[Path]:
    """Return a sorted list of all ``*.pddl`` problem files (excluding domain.pddl)
    found under each directory in *domain_dirs*."""
    files: list[Path] = []
    for d in domain_dirs:
        d = Path(d)
        for f in sorted(d.rglob("*.pddl")):
            if f.name != "domain.pddl":
                files.append(f)
    return files


def get_splits_from_config(config: dict) -> tuple[float, float, float]:
    """Extract (train, val, test) fractions from a loaded YAML config dict."""
    data = config.get("data", {})
    return (
        float(data.get("train_split", 0.70)),
        float(data.get("val_split",   0.15)),
        float(data.get("test_split",  0.15)),
    )
