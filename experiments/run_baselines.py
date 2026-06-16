from __future__ import annotations

import argparse
import json
from pathlib import Path

from cert_lgs.utils.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/default.yaml")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    out_dir = Path(config["project"]["results_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "experiment": "baseline_symbolic",
        "status": "placeholder",
        "coverage": None,
        "runtime_seconds": None,
        "memory_mb": None,
        "note": "Replace with real expressive symbolic-search baseline.",
    }

    path = out_dir / "baseline_symbolic.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
