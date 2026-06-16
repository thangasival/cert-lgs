from __future__ import annotations

import argparse
import json
from pathlib import Path

from cert_lgs.certification.certifier import CertificationLayer
from cert_lgs.learning.model import build_guidance_model
from cert_lgs.planner.symbolic_search import SymbolicSearchPlanner
from cert_lgs.utils.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    out_dir = Path(config["project"]["results_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    planner = SymbolicSearchPlanner(config)
    guide = build_guidance_model(config)
    certifier = CertificationLayer(config)

    result = planner.solve_with_guidance(guide=guide, certifier=certifier)
    payload = {
        "experiment": "cert_lgs",
        "status": result.status,
        "plan_cost": result.plan_cost,
        "expanded": result.expanded,
        "certificates_checked": result.certificates_checked,
        "certificates_rejected": result.certificates_rejected,
        "diagnostics": result.diagnostics,
    }

    path = out_dir / "cert_lgs.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
