"""Package saved POWER and optional SMAP outputs without network access."""
import argparse
import json
import sys
from pathlib import Path
from backend.services.environment import build_environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--power", type=Path, required=True)
    parser.add_argument("--smap", type=Path)
    parser.add_argument("--farm-id", required=True)
    parser.add_argument("--observation-id", required=True)
    parser.add_argument("--input-version", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("Output exists; choose another path")
        def load(path):
            return json.loads(path.read_text(encoding="utf-8-sig"))
        result = build_environment(load(args.power), args.farm_id, args.observation_id, args.input_version,
                                   load(args.smap) if args.smap else None)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(json.dumps({"climate": result["climate"]["status"], "soil_moisture": result["soil_moisture"]["status"], "date_label_overlap": result["date_label_overlap"]}, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"Environment error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
