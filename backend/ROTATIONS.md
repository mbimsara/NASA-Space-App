# Rotation API

`POST /api/v1/farms/{farm_id}/rotations` returns HTTP 200 with an immutable
analysis, including when no approved or feasible candidates exist.

Example request for a **synthetic test farm and observation** (replace both IDs
with IDs returned by the local API; no climate or crop values are asserted):

```json
{
  "input_version": 1,
  "observation_id": "replace-with-synthetic-snapshot-id",
  "seasons": 3,
  "season_labels": ["maha", "yala", "maha"],
  "catalog_version": "0.1-draft",
  "priority_weights": {"water": 0.5, "soil": 0.3, "climate": 0.2}
}
```

`seasons` must be an integer from 3 to 5. `season_labels` is an optional extension
to Shehani's count-only request: if supplied, its length must equal `seasons`;
each label is `maha`, `yala` or `inter-season`. These are explicit user-selected
labels, not a calendar inferred from farm location or observation dates. Without
labels, the analysis has no candidates and explains the missing season identity.
`observation_id` must be nonempty and non-null. Priority weights must be finite,
nonnegative and have positive total; normalized values are returned.

The response contains `analysis_id`, `farm_id`, `input_version`, `observation_id`,
`catalog_version`, `model_version`, `data_kind`, `created_at`, `candidates`,
`priority_weights`, `reasons`, `assumptions`, `source_refs` and `limitations`.
Each candidate contains a stable `candidate_id`, one-based `sequence`, nullable
`score`, `score_components`, `water_budget`, nullable `water_budget_range`,
`reasons` and `constraint_checks`. Scores are heuristic comparisons, never yield
or success predictions. Engine components disclose requested/effective weights.

The current local catalog is empty and research-pending. A valid request therefore
returns `candidates: []`, with explanations; it does not fabricate a rotation.
Catalog-wide review and individual crop approval are both required. An approved
test fixture can exercise candidate generation; fixture approval has no effect
on the production catalog. The backend does not replace the local catalog with
Bhagya's larger research-pending draft or adopt any draft numeric values.

The API loads the catalog through Bhagya's unchanged loader and calls his
candidate generator with explicit seasons, farmer exclusions and crop history.
Unapproved consecutive-crop/family policies remain disabled. Generation is capped
at 100 feasible sequences and this bound is disclosed. Ranking uses his scorer
only when a positively weighted component is available. With current inputs,
only the crop-diversity proxy can be scored; otherwise `score` is null.

Water integration is blocked by a contract gap: the persisted observation has a
single arbitrary date range, while the water functions require rainfall and
approved demand for each matching crop period. The backend must not replicate
that rainfall across future seasons. Water metrics stay null, including effective
rainfall; the response explains this. Unknown irrigation is never assumed zero.
No water cutoff, soil bonus, drainage rule or synthetic climate fallback is used.
Bhagya's reviewed demo range model does not approve the crop catalog itself.
See [engine provenance](agrosphere_rotation/VENDORED.md) and
[owner review](../docs/BHAGYA_CATALOG_REVIEW.md).

Unknown farms/observations return 404; farm version and observation ownership or
version conflicts return 409; invalid fields or installed catalog-version mismatch
return 422; malformed/unavailable catalogs, computation or storage failures return
503 using the existing error envelope. Cache expiry alone does not invalidate a
matching historical observation reference. No NASA request occurs in this endpoint.

Startup adds `rotation_analyses` through SQLAlchemy `create_all`; existing tables
and SQLite records are preserved. Each row stores farm/version/observation keys,
the original farm profile, normalized request, complete catalog snapshot, pinned
engine commit and full response JSON. Analyses and candidate IDs are allocated
once per saved analysis. Repeated POSTs create separate analyses. A conditional
no-op farm update rechecks the version and holds the SQLite writer lock until the
analysis insert commits; a concurrent farm change returns 409 without saving.

Analyses can be retrieved internally with `Session.get(RotationAnalysis, id)`;
their original input versions remain intact after farm edits. No public analysis
GET, Climate Scenario, Saved Plan or AI Assistant APIs are introduced here.

Tests use temporary SQLite databases and controlled synthetic observations/catalogs.
Run the complete suite with `PYTHONPATH=backend python -m pytest backend/tests -q`
and shared validation with `python scripts/validate_data.py` from the repository root.
