# Repeatable SMAP subset automation

Status: January 2025 authenticated live run completed and verified on 2026-11-14. All 31 subset files downloaded, validated and extracted. Independent hash verification and re-extraction matched the saved time series. Quality-filtered moisture coverage remains partial, as described below.

## Full-month verification

| Check | Result |
| --- | --- |
| NASA processing | Successful, 100% |
| Expected / supplied granule dates | 31 / 31 |
| Accepted AM retrievals | 12 |
| Accepted PM retrievals | 11 |
| Unavailable/rejected pass slots | 39 of 62 |
| Integrity and replay | All 31 SHA-256 hashes matched; independently rebuilt daily series and coverage matched saved results |
| Unified environment response | POWER complete; SMAP partial; calendar-label overlap January 1–31, 2025 |
| Automated verification | 40 tests pass; shared-data validation passes |

Private user sign-in resumed the same job from 27 ready files to all 31 without a new request. This demonstrates processing/download resumption with real NASA outputs. Files remain under ignored `.cache/smap/january-2025/`; no credentials or downloaded data are committed. A second authenticated rerun after successful completion was not performed; verified-file reuse is covered by mocked tests and independent local replay.

These counts measure accepted pass slots, not 23 distinct dates or continuous daily soil-moisture coverage. Unknown passes remain null. This sample does not establish drought or crop suitability.

Uses NASA's [official harmony-py client](https://github.com/nasa/harmony-py) and [Harmony service](https://harmony.earthdata.nasa.gov/docs). The dependency is pinned in `backend/requirements-smap.txt`. Spatial trimming is always requested for the fixed Sri Lankan demonstration box (80.3–80.5 E, 8.2–8.4 N). No global downloads, alternative providers or forecast products are requested.

## Run privately in your terminal

```powershell
.venv/Scripts/python.exe -m pip install -r backend/requirements-smap.txt
.venv/Scripts/python.exe -m scripts.run_smap_pipeline --plan
.venv/Scripts/python.exe -m scripts.run_smap_pipeline
```

The plan needs no credentials or network. The run prompts for your Earthdata username and a hidden password in your own terminal. They are passed in memory to the official client, not saved by this script. No netrc file is created, no password/token is accepted on command-line arguments, and provider exceptions are suppressed because they can contain signed URLs or authentication context. Do not enable verbose SDK/debug logging or paste credentials into chat. Any unexpected account authorization prompt should be handled by the user in NASA's interface.

Default request: SPL3SMP_E V006, January 1–31, 2025, spatially trimmed NetCDF output, both passes/all variables preserved. Request collection ID was verified through Earthdata Search. Change dates using `--start` and `--end` for a historical interval of at most 31 days; changing the box/product is intentionally not exposed in this first pipeline.

## Resume

Repeat the same command in your terminal. The job ID and request specification are saved under ignored `.cache/smap/january-2025/state.json`. The script checks the job once and downloads any ready results; it does not wait indefinitely for processing. Repeat later if NASA is still working. Existing verified files are reused, and the same directory never deliberately submits a second job.

To keep checking for up to 15 minutes with a single private sign-in, run `.venv/Scripts/python.exe -m scripts.run_smap_pipeline --watch-seconds 900`. It checks roughly every 20 seconds between syncs and stops after successful processing or the watch budget. In-flight provider requests/downloads can extend beyond that budget; Ctrl+C stops locally while preserving the remote job and completed files. Failed/paused jobs stop for inspection. The script never automatically resubmits the saved request.

If the saved submission has no job ID, its outcome is uncertain (for example, the client disconnected after NASA accepted the request). Inspect your Harmony/Earthdata job history before making any replacement request. Do not delete the manifest and blindly resubmit. Existing state with different settings is rejected; choose a separate directory for an intentional new period.

Only run one sync process per job directory. Exclusive initial state creation prevents duplicate submission; concurrent syncs are not supported. If processing fails or pauses, inspect the NASA job interface rather than automatically resubmitting. The script does not cancel remote jobs.

## Local outputs and safeguards

- `state.json`: settings, job ID, last status/progress, verified file hashes and coverage. No password/token/signed URL is written.
- `subsets/`: validated local subset files. Files are first downloaded into temporary space, inspected, then atomically promoted. At most three download/validation attempts occur per sync.
- `extracted/`: per-file AM/PM point results with quality and distance details.
- `series.json`: combined period with gaps, pass acceptance counts and provenance. It can exist while processing is still underway.

Downloads accept only HTTPS NASA Harmony or AWS service-result hosts and canonical dated SMAP subset filenames within the request period. These checks do not independently certify scientific product identity; collection/version provenance and file validation remain necessary. Corrupt existing files are revalidated and redownloaded rather than silently reused. SDK 1.8.0 also stages interrupted downloads before publishing them.

## Completion gate

Check remote status, `all_requested_dates_supplied`, `coverage.supplied_granule_days`, expected days, and separate accepted AM/PM counts. Successful processing is not proof of valid retrievals every day; a missing source date can remain a gap even after the job ends. Never interpolate missing moisture or infer drought from a short sample.

After processing, combine `series.json` with POWER using `scripts.build_environment`. Keep all cache files out of Git. Record live-run coverage and limitations in the SMAP guide only after verification.

## Tests

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
python scripts/validate_data.py
```

40 tests currently pass in the configured environment. Pipeline tests use mocks for submission reuse/uncertain submission, request restrictions, bounded retries, partial coverage, existing-file reuse and failed-download nonpublication. The official SDK separately validated the generated request; this is not a substitute for authenticated live verification.
