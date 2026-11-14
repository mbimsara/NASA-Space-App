"""Rank explicitly supplied NASA POWER histories without network access."""
import argparse
import json
import sys
from pathlib import Path
from backend.services.climate_twins import rank_twins


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--candidate", action="append", required=True, help="NAME=normalized-file.json; repeat for each site")
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--end-year", type=int, required=True)
    parser.add_argument("--rain-scale-mm", type=float, default=100)
    parser.add_argument("--temperature-scale-c", type=float, default=1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("Output exists; choose a new path")

        def load(path):
            return json.loads(Path(path).read_text(encoding="utf-8-sig"))

        candidates = []
        for item in args.candidate:
            if "=" not in item:
                raise ValueError("Use NAME=path for each candidate")
            name, path = item.split("=", 1)
            candidates.append({"name": name, "observations": load(path)})
        result = rank_twins(load(args.target), candidates, args.start_year, args.end_year, args.rain_scale_mm, args.temperature_scale_c)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        for candidate in result["ranked_candidates"]:
            print(f"{candidate['name']}: distance {candidate['distance']:.4f}")
        for candidate in result["rejected_candidates"]:
            print(f"Excluded {candidate['name']}: {candidate['reason']}")
        print(f"Saved: {args.output}")
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"Climate twin error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
