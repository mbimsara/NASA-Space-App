# Verification strategy

For the combined suite, install `backend/requirements.txt` and the local package (`python -m pip install -e .`). From the repository root in PowerShell run:

```powershell
$env:PYTHONPATH = 'backend;src'
python -m pytest tests backend/tests
```

On Linux/macOS use `PYTHONPATH=backend:src python -m pytest tests backend/tests`. Install `backend/requirements-smap.txt` as well to exercise optional SMAP file tests. In `frontend/`, run `npm ci`, `npm test`, `npm run build`, and `npm run lint`.

NASA POWER adapter tests run with `python -m unittest discover -s tests -v`, without live network access. Add further tests alongside the implementation they verify.

Backend automated tests are in `backend/tests/`. Follow [backend setup](../backend/README.md), then run `python -m pytest -q` from `backend/`. Tests cover farm APIs, validation/version conflicts, environment configuration, CORS, SQLite persistence, and observation requests/provenance/partial coverage, persistent cache reuse/expiry, concurrent fills, stale farm versions, and future analysis reference checks without live providers. The shared backend fixture blocks NASA network access. Add tests alongside further implementation.

Prioritize constraint eligibility, water units/periods, rainfall scenario recalculation, financial conversion/ranges, farm version conflicts, persistence, assistant numeric grounding, and stale frontend responses. Use approved calculation examples and synthetic inputs; do not require live NASA or AI access for routine tests.

Integration smoke checks should cover farm â†’ observations â†’ rotations â†’ scenario â†’ saved plan. Provider smoke checks are separate, explicitly configured, and must not print secrets. Mobile/accessibility and fluent-language review also require human or UI verification.

Run `python scripts/validate_data.py` for the current repository's shared sample-data checks.
