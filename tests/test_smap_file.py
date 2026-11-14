import importlib.util
import tempfile
import unittest
from pathlib import Path
from scripts.inspect_smap_file import inspect_file
from backend.services.smap_file import extract_point


@unittest.skipUnless(importlib.util.find_spec("h5py"), "Optional SMAP HDF5 dependency not installed")
class SmapFileTests(unittest.TestCase):
    def test_reads_inventory_without_claiming_science_extraction(self):
        import h5py
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "synthetic.h5"
            with h5py.File(path, "w") as file:
                dataset = file.create_dataset("Soil_Moisture_Retrieval_Data_AM/soil_moisture", data=[[0.25, -9999.]])
                dataset.attrs["units"] = "m3/m3"
                dataset.attrs["_FillValue"] = -9999.
            result = inspect_file(path)
        self.assertEqual(result["kind"], "local_hdf5_inventory_only")
        self.assertEqual(result["datasets"][0]["shape"], [1, 2])
        self.assertEqual(result["datasets"][0]["attributes"]["units"], "m3/m3")

    def test_nearest_pixel_rejection_does_not_choose_farther_valid_pixel(self):
        import h5py
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "SMAP_L3_SM_P_E_20250101_SYNTHETIC_subsetted.nc4"
            with h5py.File(path, "w") as file:
                for orbit, suffix in (("AM", ""), ("PM", "_pm")):
                    group = file.create_group(f"Soil_Moisture_Retrieval_Data_{orbit}")
                    group.create_dataset(f"latitude{suffix}", data=[[8.3, 8.35]])
                    group.create_dataset(f"longitude{suffix}", data=[[80.4, 80.4]])
                    soil = group.create_dataset(f"soil_moisture{suffix}", data=[[0.25, 0.3]])
                    soil.attrs.update(units="cm**3/cm**3", _FillValue=-9999., valid_min=0.02, valid_max=0.5)
                    group.create_dataset(f"retrieval_qual_flag{suffix}", data=[[1, 0]])
                    group.create_dataset(f"surface_flag{suffix}", data=[[0, 0]])
                    group.create_dataset(f"tb_time_utc{suffix}", data=[[b"2025-01-01T00:00:00Z", b"2025-01-01T00:00:00Z"]])
            result = extract_point(path, 8.3, 80.4)
            self.assertFalse(result["passes"][0]["accepted"])
            self.assertEqual(result["passes"][0]["subset_array_index"], [0, 0])
            self.assertEqual(result["passes"][0]["rejection_reason"], "quality_not_recommended")
            distant = extract_point(path, 7, 80.4)
            self.assertEqual(distant["passes"][0]["rejection_reason"], "nearest_pixel_too_far")
            with h5py.File(path, "a") as file:
                file['Soil_Moisture_Retrieval_Data_AM/latitude'][:] = -9999
            missing = extract_point(path, 8.3, 80.4)
            self.assertEqual(missing["passes"][0]["rejection_reason"], "no_valid_geolocation_for_pass")
