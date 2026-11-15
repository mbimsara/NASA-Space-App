"""Search and download official GPM/HLS granules with local Earthdata login.

This command never accepts credentials as command-line arguments and never writes
them to the repository. Raw provider files remain under the ignored `.cache` tree.
"""

import argparse
import importlib
from pathlib import Path


PRODUCTS = {
    "gpm": (("GPM_3IMERGDF", "07"),),
    "hls": (("HLSL30", "2.0"), ("HLSS30", "2.0")),
}


def search_arguments(short_name, version, latitude, longitude, start, end, count):
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Coordinates are outside WGS84 bounds.")
    if count < 1 or count > 500:
        raise ValueError("Count must be between 1 and 500.")
    return {
        "short_name": short_name,
        "version": version,
        "temporal": (start, end),
        "bounding_box": (longitude - 0.001, latitude - 0.001,
                         longitude + 0.001, latitude + 0.001),
        "count": count,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("product", choices=PRODUCTS)
    parser.add_argument("--latitude", type=float, required=True)
    parser.add_argument("--longitude", type=float, required=True)
    parser.add_argument("--start", required=True, help="ISO date or datetime")
    parser.add_argument("--end", required=True, help="ISO date or datetime")
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        earthaccess = importlib.import_module("earthaccess")
    except ModuleNotFoundError as exc:
        raise SystemExit("Install backend/requirements-earthdata.txt first.") from exc

    # earthaccess checks .netrc/environment first and otherwise prompts locally.
    # No token, username or password is logged by this script.
    earthaccess.login()
    destination = args.output or Path(".cache") / args.product / "raw"
    destination.mkdir(parents=True, exist_ok=True)
    downloaded = []
    for short_name, version in PRODUCTS[args.product]:
        query = search_arguments(short_name, version, args.latitude, args.longitude,
                                 args.start, args.end, args.count)
        granules = earthaccess.search_data(**query)
        if not granules:
            print(f"No {short_name} {version} granules matched the requested point and dates.")
            continue
        paths = earthaccess.download(granules, local_path=str(destination))
        downloaded.extend(str(path) for path in paths if path)
        print(f"{short_name} {version}: downloaded {len(paths)} file(s) to {destination}")
    if not downloaded:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
