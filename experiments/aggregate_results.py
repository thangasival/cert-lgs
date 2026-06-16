from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", default="results/raw")
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    rows = []
    for path in results_dir.glob("*.json"):
        rows.append(json.loads(path.read_text(encoding="utf-8")))

    df = pd.DataFrame(rows)
    out_dir = Path("results/tables")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "summary.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
