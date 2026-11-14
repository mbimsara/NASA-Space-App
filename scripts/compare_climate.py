"""Compare a target year to a historical reference in a saved POWER series."""
import argparse
import json
import sys
from pathlib import Path
from backend.services.climate_baseline import compare_monthly


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reference-start", type=int, required=True)
    parser.add_argument("--reference-end", type=int, required=True)
    parser.add_argument("--target-year", type=int, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("Output already exists; choose another path")
        source = json.loads(args.input.read_text(encoding="utf-8-sig"))
        result = compare_monthly(source, args.reference_start, args.reference_end, args.target_year)
        result.update({key: source[key] for key in ("provider", "sources", "coordinates", "data_kind")})
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        for month in result["monthly"]:
            print(f"Month {month['month']:02}: rainfall difference = {month['rainfall_difference_pct']}%")
        print(f"Saved: {args.output}")
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"Climate comparison error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
