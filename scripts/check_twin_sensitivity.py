"""Evaluate a fixed exploratory grid of rainfall and temperature scales."""
import argparse
import json
import sys
from pathlib import Path
from backend.services.twin_sensitivity import sensitivity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("Output exists; choose another path")
        ranking = json.loads(args.input.read_text(encoding="utf-8-sig"))
        result = sensitivity(ranking, [{"rainfall_mm": r, "temperature_c": t} for r in (50, 100, 200) for t in (0.5, 1, 2)])
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"Best set unchanged across tested scales: {result['best_set_unchanged_in_tested_settings']}")
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"Sensitivity error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
