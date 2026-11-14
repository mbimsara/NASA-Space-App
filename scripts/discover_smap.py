"""Discover SMAP sample metadata from NASA CMR without authentication."""
import argparse
import json
import sys
from pathlib import Path
from backend.services.smap import discover


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--latitude", type=float, default=8.3)
    parser.add_argument("--longitude", type=float, default=80.4)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("Output exists; choose another path")
        result = discover(args.latitude, args.longitude, args.start, args.end)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        print(f"Found {len(result['granules'])} sample granules; metadata only. Truncated: {result['truncated']}")
        print(f"Saved: {args.output}")
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"SMAP discovery error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
