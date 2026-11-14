Source: `mbimsara/NASA-Space-App`, branch `zerokali20`, commit
`5407f56a2f81615ecaab72a780e0da096ba03f83`.

The seven Python files in this directory are byte-for-byte copies of
`src/agrosphere_rotation/` at that commit. No formulas, defaults or approval
decisions were changed. This location makes the package importable using the
existing backend startup and CI PYTHONPATH without merging branches or adding
runtime Git/network dependencies. Update all files together after owner review.

The API uses `catalog.load_catalog`, `rotation.generate_candidates` and
`scoring.rank_candidates`. Water functions are preserved but are deliberately
not called with the current observation contract: no approved mapping identifies
each crop's matching rainfall/demand period. A single observation total cannot
be repeated across three to five seasons. Integrating those functions requires
an agreed seasonal climate handoff and approved crops, not new backend formulas.
