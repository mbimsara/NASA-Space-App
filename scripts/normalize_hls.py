"""Normalize a trusted CSV export of quality-screened NASA HLS NDVI observations."""
import argparse, csv, json, sys
from pathlib import Path
from backend.services.hls_vegetation import normalize_observations

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--latitude", type=float, required=True); parser.add_argument("--longitude", type=float, required=True)
    parser.add_argument("--source", action="append", required=True)
    args = parser.parse_args()
    try:
        if args.output.exists(): raise ValueError("Output exists")
        with args.input.open(encoding="utf-8-sig", newline="") as stream:
            rows = []
            for row in csv.DictReader(stream):
                accepted = row["quality_accepted"].strip().lower() == "true"
                rows.append({"date": row["date"], "product": row["product"], "ndvi": float(row["ndvi"]) if accepted and row["ndvi"].strip() else None,
                             "cloud_percent": float(row["cloud_percent"]), "quality_accepted": accepted,
                             "rejection_reason": row.get("rejection_reason") or None})
        result = normalize_observations(rows, latitude=args.latitude, longitude=args.longitude, source_refs=args.source)
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    except (OSError, ValueError, KeyError) as error: print(f"HLS error: {error}", file=sys.stderr); return 1
    return 0
if __name__ == "__main__": sys.exit(main())
