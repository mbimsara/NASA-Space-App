"""Run from repo root: python -m scripts.nasa_power --help."""
import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError

from backend.services.nasa_power import fetch, normalize, request_url


def main():
    parser = argparse.ArgumentParser(description="NASA POWER rainfall/temperature adapter")
    parser.add_argument("--latitude", type=float, default=8.3)
    parser.add_argument("--longitude", type=float, default=80.4)
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--input", type=Path, help="Normalize a previously downloaded JSON response, without network access")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include-extremes", action="store_true", help="Also request T2M_MAX and T2M_MIN")
    parser.add_argument("--refresh", action="store_true", help="Replace an existing output by explicitly fetching again")
    args = parser.parse_args()
    try:
        if args.output.exists() and not args.refresh:
            raise ValueError("Output already exists; choose another output or explicitly use --refresh")
        url = request_url(args.latitude, args.longitude, args.start, args.end, args.include_extremes)
        if args.input:
            raw = json.loads(args.input.read_text(encoding="utf-8-sig"))
            retrieved_at = None
            coordinates = raw["geometry"]["coordinates"]
            if abs(coordinates[0] - args.longitude) > 0.0001 or abs(coordinates[1] - args.latitude) > 0.0001:
                raise ValueError("Imported coordinates differ from requested coordinates")
        else:
            raw, retrieved_at, url = fetch(args.latitude, args.longitude, args.start, args.end, args.include_extremes)
        if args.include_extremes and not {"T2M_MAX", "T2M_MIN"} <= raw["properties"]["parameter"].keys():
            raise ValueError("Requested extremes are absent from the response")
        result = normalize(raw, args.start, args.end, retrieved_at, url)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps(result["summary"], indent=2))
        print(f"Saved: {args.output}")
    except (ValueError, KeyError, TypeError, OSError, HTTPError, URLError) as error:
        print(f"NASA POWER error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
