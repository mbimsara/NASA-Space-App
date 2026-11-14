"""Resumable, small Sri Lankan Harmony subset jobs. No credentials in state."""
import json
import os
import re
import tempfile
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote
from backend.services.smap_file import extract_point
from backend.services.smap_series import build_series

COLLECTION = "C2938664763-NSIDC_CPRD"


def specification(start, end):
    first, last = date.fromisoformat(start), date.fromisoformat(end)
    if (start != first.isoformat() or end != last.isoformat() or first < date(2015, 3, 31)
            or last >= datetime.now(timezone.utc).date() or not 0 <= (last - first).days <= 30):
        raise ValueError("Use an inclusive historical interval of 1–31 days within SMAP coverage")
    return {"collection_id": COLLECTION, "product": "SPL3SMP_E", "version": "006",
            "start": start, "end": end, "bbox": [80.3, 8.2, 80.5, 8.4],
            "latitude": 8.3, "longitude": 80.4, "max_distance_km": 15}


def request_for(spec):
    from harmony import Request, Collection, BBox
    return Request(collection=Collection(id=COLLECTION), spatial=BBox(*spec["bbox"]),
                   temporal={"start": datetime.fromisoformat(spec["start"] + "T00:00:00+00:00"),
                             "stop": datetime.fromisoformat(spec["end"] + "T23:59:59+00:00")},
                   format="application/netcdf", skip_preview=True, ignore_errors=False,
                   max_results=100)


def save(path, value):
    """Atomic JSON replacement, so interruption cannot publish half a manifest."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def prepare(root, spec, client):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    path = root / "state.json"
    if path.exists():
        state = json.loads(path.read_text(encoding="utf-8"))
        if state["specification"] != spec:
            raise ValueError("Existing state uses different request settings; choose another directory")
        if not state.get("job_id"):
            raise ValueError("Previous submission outcome is unknown; inspect Harmony history before any new submission")
        return state
    state = {"schema_version": "0.1", "specification": spec, "status": "submitting", "files": {}}
    # Exclusive creation prevents a second process from submitting the same directory.
    with path.open("x", encoding="utf-8") as stream:
        json.dump(state, stream)
    job_id = client.submit(request_for(spec))
    state.update(job_id=str(job_id), status="submitted")
    save(path, state)
    return state


def canonical_name(url, spec):
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if parsed.scheme != "https" or not (host == "harmony.earthdata.nasa.gov" or host.endswith(".amazonaws.com")):
        raise ValueError("Unexpected result host")
    name = unquote(parsed.path.rsplit("/", 1)[-1])
    match = re.fullmatch(r"SMAP_L3_SM_P_E_(\d{8})_[A-Za-z0-9_]+_subsetted\.(?:nc4|h5)", name)
    if not match:
        raise ValueError("Unexpected subset file name; full global files are not accepted")
    day = datetime.strptime(match.group(1), "%Y%m%d").date().isoformat()
    if not spec["start"] <= day <= spec["end"]:
        raise ValueError("Result date is outside requested interval")
    return name


def sync(root, state, client, attempts=3, pause=time.sleep):
    """Check once, then download ready results. Resume by calling again."""
    root = Path(root)
    spec = state["specification"]
    status = client.status(state["job_id"])
    state["status"] = str(status["status"]).lower()
    state["progress"] = status.get("progress")
    state["checked_at"] = datetime.now(timezone.utc).isoformat()
    save(root / "state.json", state)
    if state["status"] in ("failed", "canceled", "cancelled", "paused"):
        raise ValueError("Harmony job needs attention; inspect it in the NASA job interface")
    raw_dir = root / "subsets"
    raw_dir.mkdir(exist_ok=True)
    for url in client.result_urls(state["job_id"], allow_incomplete=True):
        name = canonical_name(url, spec)
        target = raw_dir / name
        try:
            record = extract_point(target, spec["latitude"], spec["longitude"], spec["max_distance_km"]) if target.exists() else None
        except (ValueError, KeyError, OSError):
            record = None
        if record is None:
            for attempt in range(attempts):
                try:
                    with tempfile.TemporaryDirectory(dir=root) as folder:
                        downloaded = Path(client.download(url, directory=folder, overwrite=False).result(timeout=90))
                        # SDK prefixes staged names. Rename within temp space before validation.
                        canonical = Path(folder) / name
                        if downloaded != canonical:
                            downloaded.rename(canonical)
                        record = extract_point(canonical, spec["latitude"], spec["longitude"], spec["max_distance_km"])
                        os.replace(canonical, target)
                    break
                except Exception:
                    # Never print provider exceptions: they can contain signed URLs or auth context.
                    if attempt + 1 == attempts:
                        state["files"][name] = {"status": "retry_needed"}
                        save(root / "state.json", state)
                        raise ValueError("Subset download/validation failed after bounded retries; rerun to resume") from None
                    pause(min(2 ** attempt, 4))
        record["downloaded_from_job"] = state["job_id"]
        save(root / "extracted" / (name + ".json"), record)
        state["files"][name] = {"status": "verified", "sha256": record["sha256"]}
        save(root / "state.json", state)
    records = [json.loads(path.read_text(encoding="utf-8")) for path in (root / "extracted").glob("*.json")] if (root / "extracted").exists() else []
    if records:
        series = build_series(records, spec["start"], spec["end"])
        save(root / "series.json", series)
        state["coverage"] = series["coverage"]
    state["all_requested_dates_supplied"] = state.get("coverage", {}).get("supplied_granule_days", 0) == (date.fromisoformat(spec["end"]) - date.fromisoformat(spec["start"])).days + 1
    save(root / "state.json", state)
    return state
