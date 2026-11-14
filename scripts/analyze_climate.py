"""Analyze a saved normalized POWER response without network access."""
import argparse
import json
import sys
from pathlib import Path
from backend.services.climate import historical_indicators, rainfall_scenario


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rainfall-change-pct", type=float, default=-30)
    parser.add_argument("--dry-below-mm", type=float, default=1)
    parser.add_argument("--warm-at-or-above-c", type=float, default=30)
    parser.add_argument("--rain-at-or-above-mm", type=float, default=20)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("Output exists; choose a new output path")
        observations = json.loads(args.input.read_text(encoding="utf-8-sig"))
        result = {
            "schema_version": "0.1", "provider": observations["provider"],
            "coordinates": observations["coordinates"], "sources": observations["sources"],
            "source_url": observations["source_url"], "retrieved_at": observations["retrieved_at"],
            "data_kind": observations["data_kind"],
            "historical": historical_indicators(observations, args.dry_below_mm, args.warm_at_or_above_c, args.rain_at_or_above_mm),
            "scenario": rainfall_scenario(observations, args.rainfall_change_pct),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps({"historical": result["historical"], "scenario_summary": result["scenario"]["summary"]}, indent=2))
        print(f"Saved: {args.output}")
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"Climate analysis error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
