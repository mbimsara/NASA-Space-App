"""Extract a quality-filtered point from a downloaded Sri Lankan SMAP subset."""
import argparse
import json
import sys
from pathlib import Path
from backend.services.smap_file import extract_point


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--latitude", type=float, default=8.3)
    parser.add_argument("--longitude", type=float, default=80.4)
    parser.add_argument("--max-distance-km", type=float, default=15)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("Output exists; choose another path")
        result = extract_point(args.input, args.latitude, args.longitude, args.max_distance_km)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps(result["passes"], indent=2))
    except (ImportError, ValueError, KeyError, OSError) as error:
        print(f"SMAP extraction error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
