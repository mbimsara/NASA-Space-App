"""Inventory a local NASA subset without treating metadata as valid retrievals."""
import argparse
import json
import sys
from pathlib import Path


def inspect_file(path):
    try:
        import h5py
    except ImportError as error:
        raise RuntimeError("Install backend/requirements-smap.txt in a local virtual environment") from error
    datasets = []

    def convert(value):
        if hasattr(value, "tolist"):
            value = value.tolist()
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        if isinstance(value, (list, tuple)):
            return [convert(item) for item in value]
        if isinstance(value, float) and not __import__("math").isfinite(value):
            return str(value)
        return value

    with h5py.File(path, "r") as file:
        def visit(name, obj):
            if isinstance(obj, h5py.Dataset):
                attrs = {key: convert(obj.attrs[key]) for key in (
                    "units", "_FillValue", "valid_min", "valid_max", "long_name", "coordinates") if key in obj.attrs}
                datasets.append({"path": name, "shape": list(obj.shape), "dtype": str(obj.dtype), "attributes": attrs})
        file.visititems(visit)
    return {"file_name": Path(path).name, "kind": "local_hdf5_inventory_only", "datasets": datasets,
            "limitations": ["No pixel selected or quality-filtered; this inventory is not a soil-moisture result."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("Output exists; choose another path")
        result = inspect_file(args.input)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"Inventoried {len(result['datasets'])} datasets; no science extraction performed.")
    except (RuntimeError, ValueError, OSError) as error:
        print(f"SMAP inspection error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
