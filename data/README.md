# Shared data

`fixtures/farm.synthetic.json` contains invented demonstration inputs, not a real farmer's records. Unknown measurements remain null. `catalogs/crops.json` is intentionally empty until Tharuka researches entries and Bhagya approves them; it cannot generate recommendations yet.

Schemas describe the proposed shared format. Keep schemas, API contracts, fixtures, and validation aligned. Preserve units, evidence links, review status and versions. Never commit private farmer records or field photos.

Run `python scripts/validate_data.py` from the repository root (Python 3.10+, standard library only). The validator checks the repository's contract fields, not arbitrary JSON Schema documents.
