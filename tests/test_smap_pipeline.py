import copy
import json
import tempfile
import unittest
from concurrent.futures import Future
from pathlib import Path
from unittest.mock import Mock, patch
from backend.services.smap_pipeline import specification, prepare, sync, canonical_name
from test_smap_series import record

NAME = "SMAP_L3_SM_P_E_20250101_R19240_001_subsetted.nc4"
URL = "https://harmony.earthdata.nasa.gov/service-results/example/" + NAME


class PipelineTests(unittest.TestCase):
    def test_submission_reused_and_uncertain_submit_not_repeated(self):
        spec = specification("2025-01-01", "2025-01-03")
        with tempfile.TemporaryDirectory() as folder, patch("backend.services.smap_pipeline.request_for"):
            client = Mock()
            client.submit.return_value = "job-example"
            self.assertEqual(prepare(folder, spec, client)["job_id"], "job-example")
            prepare(folder, spec, client)
            self.assertEqual(client.submit.call_count, 1)
            with self.assertRaises(ValueError):
                prepare(folder, specification("2025-01-01", "2025-01-04"), client)
        with tempfile.TemporaryDirectory() as folder, patch("backend.services.smap_pipeline.request_for"):
            client.submit.side_effect = RuntimeError("private provider error")
            with self.assertRaises(RuntimeError):
                prepare(folder, spec, client)
            client.submit.reset_mock()
            with self.assertRaises(ValueError):
                prepare(folder, spec, client)
            client.submit.assert_not_called()

    def test_result_names_hosts_and_dates_are_restricted(self):
        spec = specification("2025-01-01", "2025-01-03")
        self.assertEqual(canonical_name(URL, spec), NAME)
        for bad in (URL.replace("https://", "http://"), URL.replace("harmony.earthdata.nasa.gov", "example.test"),
                    URL.replace("20250101", "20250201"), URL.replace("_subsetted", "")):
            with self.assertRaises(ValueError):
                canonical_name(bad, spec)

    def test_bounded_retry_and_existing_file_reuse(self):
        with tempfile.TemporaryDirectory() as folder:
            state = {"job_id": "example", "specification": specification("2025-01-01", "2025-01-03"), "files": {}}
            client = Mock()
            client.status.return_value = {"status": "running", "progress": 20}
            client.result_urls.return_value = [URL]
            count = [0]
            def download(url, directory, overwrite):
                count[0] += 1
                if count[0] == 1:
                    raise OSError("private signed URL omitted")
                target = Path(directory) / ("123_" + NAME)
                target.write_bytes(b"synthetic")
                future = Future()
                future.set_result(str(target))
                return future
            client.download.side_effect = download
            sample = record()
            sample["file_name"] = NAME
            with patch("backend.services.smap_pipeline.extract_point", return_value=sample):
                result = sync(folder, state, client, pause=lambda seconds: None)
                self.assertEqual(count[0], 2)
                self.assertEqual(result["coverage"]["supplied_granule_days"], 1)
                sync(folder, result, client, pause=lambda seconds: None)
                self.assertEqual(count[0], 2)
            saved = json.loads((Path(folder) / "state.json").read_text())
            self.assertNotIn("private", json.dumps(saved))
            self.assertFalse(saved["all_requested_dates_supplied"])

    def test_download_failure_does_not_publish_subset(self):
        with tempfile.TemporaryDirectory() as folder:
            state = {"job_id": "example", "specification": specification("2025-01-01", "2025-01-03"), "files": {}}
            client = Mock()
            client.status.return_value = {"status": "running"}
            client.result_urls.return_value = [URL]
            client.download.side_effect = OSError("private")
            with self.assertRaises(ValueError):
                sync(folder, state, client, attempts=2, pause=lambda seconds: None)
            self.assertEqual(client.download.call_count, 2)
            self.assertFalse((Path(folder) / "subsets" / NAME).exists())
