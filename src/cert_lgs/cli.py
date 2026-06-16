from __future__ import annotations

import argparse
from pathlib import Path

from cert_lgs.certification.certifier import CertificationLayer
from cert_lgs.learning.model import build_guidance_model
from cert_lgs.planner.symbolic_search import SymbolicSearchPlanner
from cert_lgs.utils.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Cert-LGS starter pipeline.")
    parser.add_argument("--config", type=str, default="configs/default.yaml")
    args = parser.parse_args()

    config = load_config(Path(args.config))

    planner = SymbolicSearchPlanner(config=config)
    guide = build_guidance_model(config=config)
    certifier = CertificationLayer(config=config)

    result = planner.solve_with_guidance(guide=guide, certifier=certifier)

    print("=== Cert-LGS run completed ===")
    print(f"status: {result.status}")
    print(f"plan_cost: {result.plan_cost}")
    print(f"expanded: {result.expanded}")
    print(f"certificates_checked: {result.certificates_checked}")
    print(f"certificates_rejected: {result.certificates_rejected}")


if __name__ == "__main__":
    main()
