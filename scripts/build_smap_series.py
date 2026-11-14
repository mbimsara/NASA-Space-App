"""Combine explicitly selected extracted SMAP JSON files."""
import argparse
import json
import sys
from pathlib import Path
from backend.services.smap_series import build_series


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, action="append", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("Output exists; choose another path")
        records = [json.loads(path.read_text(encoding="utf-8-sig")) for path in args.input]
        result = build_series(records, args.start, args.end)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps(result["coverage"], indent=2))
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"SMAP series error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
