"""Read the nearest global-grid pixel in a local SPL3SMP_E Harmony subset."""
import hashlib
import math
import re
from pathlib import Path
from backend.services.smap import quality_filter, DOI


def extract_point(path, latitude, longitude, max_distance_km=15):
    import h5py
    import numpy as np

    for value in (latitude, longitude, max_distance_km):
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError("Coordinates and distance must be finite numbers")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180 or max_distance_km <= 0:
        raise ValueError("Invalid point or maximum distance")
    path = Path(path)
    match = re.match(r"SMAP_L3_SM_P_E_(\d{8})_.*\.(?:nc4|h5)$", path.name)
    if not match:
        raise ValueError("Expected a named SPL3SMP_E HDF5/NetCDF-4 subset")
    passes = []
    with h5py.File(path, "r") as file:
        for orbit, suffix in (("AM", ""), ("PM", "_pm")):
            group = file[f"Soil_Moisture_Retrieval_Data_{orbit}"]
            lat_ds, lon_ds = group[f"latitude{suffix}"], group[f"longitude{suffix}"]
            sm = group[f"soil_moisture{suffix}"]
            units = sm.attrs["units"]
            if isinstance(units, bytes):
                units = units.decode()
            if units not in ("cm**3/cm**3", "m3/m3", "cm3/cm3"):
                raise ValueError("Unsupported soil-moisture units")
            lat, lon = lat_ds[:], lon_ds[:]
            if lat.shape != lon.shape or lat.shape != sm.shape or lat.ndim != 2:
                raise ValueError("Expected matching 2D global-grid arrays")
            valid = np.isfinite(lat) & np.isfinite(lon) & (np.abs(lat) <= 90) & (np.abs(lon) <= 180)
            dlat = np.radians(lat.astype(float) - latitude)
            dlon = np.radians(lon.astype(float) - longitude)
            a = np.sin(dlat / 2)**2 + math.cos(math.radians(latitude)) * np.cos(np.radians(lat.astype(float))) * np.sin(dlon / 2)**2
            distance = 6371.0088 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
            distance = np.where(valid, distance, np.inf)
            if not np.any(valid):
                passes.append({"pass": orbit, "accepted": False, "soil_moisture_m3_m3": None,
                               "rejection_reason": "no_valid_geolocation_for_pass"})
                continue
            index = np.unravel_index(np.argmin(distance), distance.shape)
            km = float(distance[index])
            value = float(sm[index])
            flag = int(group[f"retrieval_qual_flag{suffix}"][index])
            filtered = quality_filter(value, flag, float(sm.attrs["_FillValue"]))
            if filtered["accepted"] and not float(sm.attrs["valid_min"]) <= value <= float(sm.attrs["valid_max"]):
                filtered.update(accepted=False, soil_moisture_m3_m3=None, rejection_reason="outside_product_valid_bounds")
            if km > max_distance_km:
                filtered.update(accepted=False, soil_moisture_m3_m3=None, rejection_reason="nearest_pixel_too_far")
            time_values = np.asarray(group[f"tb_time_utc{suffix}"][index])
            time_string = time_values.tobytes().decode("utf-8", errors="replace").strip("\x00 ")
            passes.append({"pass": orbit, "pixel_latitude": float(lat[index]), "pixel_longitude": float(lon[index]),
                           "distance_km": km, "subset_array_index": [int(i) for i in index],
                           "acquisition_time_utc_raw": time_string,
                           "surface_flag": int(group[f"surface_flag{suffix}"][index]),
                           "input_units": str(units), **filtered})
    return {
        "schema_version": "0.1", "data_kind": "satellite_retrieval", "product": "SPL3SMP_E", "version": "006",
        "product_version_basis": "Selected V006 collection in Earthdata; not independently inferred from file name.",
        "doi": DOI, "file_name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "file_date_label": match.group(1), "requested_point": {"latitude": latitude, "longitude": longitude},
        "grid_posting_km": 9, "max_distance_km": max_distance_km, "passes": passes,
        "limitations": ["Surface soil-moisture context, not field nutrients, root-zone moisture or irrigation demand.",
                        "Nearest geolocated pixel is chosen before quality filtering; rejected pixels are not replaced by farther ones.",
                        "AM/PM retrievals are retained separately and not averaged or interpolated.",
                        "Dimensionless volume ratios in cm3/cm3 equal m3/m3 numerically.",
                        "Raw acquisition-time strings are retained; fill/unavailable times must not be treated as valid timestamps."]}
