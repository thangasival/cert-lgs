from __future__ import annotations

import argparse
import json
from pathlib import Path

from cert_lgs.utils.config import load_config


ABLATIONS = [
    "no_learning",
    "random_guidance",
    "no_certifier",
    "no_partition_certificate",
    "no_admissible_bound_certificate",
    "no_transition_certificate",
    "uncalibrated_learning",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    out_dir = Path(config["project"]["results_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for ablation in ABLATIONS:
        rows.append(
            {
                "ablation": ablation,
                "status": "placeholder",
                "expected_question": "Does this component protect correctness or improve efficiency?",
            }
        )

    path = out_dir / "ablations.json"
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
