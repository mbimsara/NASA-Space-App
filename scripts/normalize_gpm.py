"""Normalize a trusted CSV export of NASA GPM IMERG daily point precipitation."""
import argparse, csv, json, sys
from pathlib import Path
from backend.services.gpm_imerg import normalize_daily

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--latitude", type=float, required=True); parser.add_argument("--longitude", type=float, required=True)
    parser.add_argument("--start", required=True); parser.add_argument("--end", required=True)
    parser.add_argument("--source", action="append", required=True)
    args = parser.parse_args()
    try:
        if args.output.exists(): raise ValueError("Output exists")
        with args.input.open(encoding="utf-8-sig", newline="") as stream:
            rows = [{"date": row["date"], "precipitation_mm": None if not row["precipitation_mm"].strip() else float(row["precipitation_mm"])} for row in csv.DictReader(stream)]
        result = normalize_daily(rows, latitude=args.latitude, longitude=args.longitude, start=args.start, end=args.end, source_refs=args.source)
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    except (OSError, ValueError, KeyError) as error: print(f"GPM error: {error}", file=sys.stderr); return 1
    return 0
if __name__ == "__main__": sys.exit(main())
