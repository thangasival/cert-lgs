"""Generate distribution-shift problem instances for Group 3 benchmark.

Three splits:
  train (p01–p10): 2 cities, 3–4 locations each, 1–2 trucks, 2–3 packages
  test  (p11–p20): 4 cities, 4–6 locations each, 2–3 trucks, 5–7 packages
  ood   (p21–p25): 6 cities, linear-chain topology (differs from train grid topology)

Usage:
    python benchmarks/distribution_shift/generate_problems.py \
           --out benchmarks/distribution_shift --seed 42
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path


# ---------------------------------------------------------------------------
# Graph topologies
# ---------------------------------------------------------------------------

def _grid_adjacency(locs_per_city: int) -> list[tuple[int, int]]:
    """Chain adjacency within a city: loc0-loc1-loc2-..."""
    return [(i, i + 1) for i in range(locs_per_city - 1)]


def _star_adjacency(locs_per_city: int) -> list[tuple[int, int]]:
    """Star around loc0: loc0-loc1, loc0-loc2, ..."""
    return [(0, i) for i in range(1, locs_per_city)]


def _make_problem(
    name: str,
    n_cities: int,
    locs_per_city: list[int],
    n_trucks: int,
    n_packages: int,
    topology: str,  # 'chain' | 'star'
    congestion_prob: float,
    seed: int,
) -> str:
    rng = random.Random(seed)

    # Build location and city lists
    city_names = [f"city{c}" for c in range(n_cities)]
    loc_names: list[list[str]] = []
    all_locs: list[str] = []
    for c, n_locs in enumerate(locs_per_city):
        city_locs = [f"loc{c}_{i}" for i in range(n_locs)]
        loc_names.append(city_locs)
        all_locs.extend(city_locs)

    # Trucks: one per city (up to n_trucks)
    truck_names = [f"truck{t}" for t in range(n_trucks)]

    # Packages
    pkg_names = [f"pkg{p}" for p in range(n_packages)]

    # Build PDDL objects block
    cities_str  = " ".join(city_names) + " - city"
    locs_str    = " ".join(all_locs)   + " - location"
    trucks_str  = " ".join(truck_names) + " - truck"
    pkgs_str    = " ".join(pkg_names)   + " - package"

    # city membership
    in_city_facts: list[str] = []
    for c, city_locs in enumerate(loc_names):
        for loc in city_locs:
            in_city_facts.append(f"(in-city {loc} {city_names[c]})")

    # adjacency within cities
    adj_facts: list[str] = []
    for c, city_locs in enumerate(loc_names):
        n = len(city_locs)
        if topology == "star":
            pairs = _star_adjacency(n)
        else:
            pairs = _grid_adjacency(n)
        for (i, j) in pairs:
            adj_facts.append(f"(adjacent {city_locs[i]} {city_locs[j]})")
            adj_facts.append(f"(adjacent {city_locs[j]} {city_locs[i]})")

    # congestion
    cong_facts: list[str] = []
    for loc in all_locs:
        if rng.random() < congestion_prob:
            cong_facts.append(f"(congested {loc})")

    # truck positions: spread across cities
    truck_facts: list[str] = []
    for t, truck in enumerate(truck_names):
        city_idx = t % n_cities
        truck_facts.append(f"(at-truck {truck} {loc_names[city_idx][0]})")

    # package positions: random
    pkg_facts: list[str] = []
    pkg_start_locs: list[str] = []
    for pkg in pkg_names:
        loc = rng.choice(all_locs)
        pkg_facts.append(f"(at-package {pkg} {loc})")
        pkg_start_locs.append(loc)

    # goals: move each package to a different city's first location
    goal_locs: list[str] = []
    for idx, _ in enumerate(pkg_names):
        target_city = (idx + 1) % n_cities
        goal_locs.append(loc_names[target_city][0])

    goal_str = "\n             ".join(
        f"(at-package {pkg} {goal})"
        for pkg, goal in zip(pkg_names, goal_locs)
    )

    all_facts = in_city_facts + adj_facts + cong_facts + truck_facts + pkg_facts
    init_str = "\n    ".join(all_facts)

    return f"""\
; Distribution-shift problem {name}
; Cities: {n_cities}, Packages: {n_packages}, Trucks: {n_trucks}, Topology: {topology}
(define (problem {name})
  (:domain distribution-shift)
  (:objects
    {cities_str}
    {locs_str}
    {trucks_str}
    {pkgs_str})
  (:init
    {init_str}
    (= (total-cost) 0))
  (:goal (and {goal_str}))
  (:metric minimize (total-cost))
)
"""


# ---------------------------------------------------------------------------
# Split definitions
# ---------------------------------------------------------------------------

SPLITS = {
    "train": {
        "n_problems": 10,
        "n_cities": 2,
        "locs_per_city": [3, 3],
        "n_trucks": 2,
        "n_packages": 3,
        "topology": "chain",
        "congestion": 0.2,
        "prefix": "p",
        "offset": 1,
    },
    "test": {
        "n_problems": 10,
        "n_cities": 4,
        "locs_per_city": [4, 4, 5, 4],
        "n_trucks": 3,
        "n_packages": 6,
        "topology": "chain",
        "congestion": 0.25,
        "prefix": "p",
        "offset": 11,
    },
    "ood": {
        "n_problems": 5,
        "n_cities": 6,
        "locs_per_city": [3, 3, 3, 3, 3, 3],
        "n_trucks": 4,
        "n_packages": 8,
        "topology": "star",   # different from train topology
        "congestion": 0.35,
        "prefix": "p",
        "offset": 21,
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate distribution-shift problems")
    parser.add_argument("--out", default="benchmarks/distribution_shift")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    for split_name, cfg in SPLITS.items():
        split_dir = out / split_name
        split_dir.mkdir(exist_ok=True)
        for idx in range(cfg["n_problems"]):
            prob_num = cfg["offset"] + idx
            name = f"{cfg['prefix']}{prob_num:02d}_{split_name}"
            prob_str = _make_problem(
                name=name,
                n_cities=cfg["n_cities"],
                locs_per_city=cfg["locs_per_city"],
                n_trucks=cfg["n_trucks"],
                n_packages=cfg["n_packages"],
                topology=cfg["topology"],
                congestion_prob=cfg["congestion"],
                seed=args.seed + prob_num,
            )
            path = split_dir / f"{name}.pddl"
            path.write_text(prob_str)
            print(f"Wrote {path}")


if __name__ == "__main__":
    main()
