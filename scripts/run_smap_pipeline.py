"""Run in your own terminal; credentials are hidden and never persisted."""
import argparse
import getpass
import json
import os
import sys
from pathlib import Path
from backend.services.smap_pipeline import specification, prepare, sync


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2025-01-01")
    parser.add_argument("--end", default="2025-01-31")
    parser.add_argument("--directory", type=Path, default=Path(".cache/smap/january-2025"))
    parser.add_argument("--plan", action="store_true", help="Show settings without authentication or network access")
    args = parser.parse_args()
    try:
        spec = specification(args.start, args.end)
        if args.plan:
            print(json.dumps(spec, indent=2))
            return 0
        if not sys.stdin.isatty():
            raise ValueError("Run in your own interactive terminal for private authentication")
        from harmony import Client
        # SDK supports explicit auth; do not save a netrc or load credentials from repo files.
        os.environ["VERBOSE"] = "FALSE"
        username = input("Earthdata username (local only): ")
        password = getpass.getpass("Earthdata password (hidden; not saved): ")
        client = Client(auth=(username, password), check_interval=10)
        state = prepare(args.directory, spec, client)
        print("NASA job ID:", state["job_id"], flush=True)
        state = sync(args.directory, state, client)
        print(json.dumps({key: state.get(key) for key in ("status", "progress", "coverage", "all_requested_dates_supplied")}, indent=2))
        if state["status"] != "successful":
            print("Processing may still be running. Repeat the same command to resume the saved job; no new submission is made.")
        return 0
    except (Exception, KeyboardInterrupt):
        print("Pipeline stopped. Credentials/provider errors are not printed. Inspect local state and NASA job history, then resume the same directory.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
