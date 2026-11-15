"""Consistent SQLite backup to a new file; never overwrite an existing backup."""
import argparse
import os
from pathlib import Path
import sqlite3


def backup(source: Path, destination: Path):
    source, destination = source.resolve(strict=True), destination.absolute()
    # Exclusive reservation protects previous backups and the source itself.
    fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        with sqlite3.connect(source.as_uri() + "?mode=ro", uri=True) as reader:
            with sqlite3.connect(destination) as writer:
                reader.backup(writer)
                if writer.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("Backup integrity check failed")
    except Exception:
        destination.unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    backup(args.source, args.destination)
    print("SQLite backup completed and verified.")
