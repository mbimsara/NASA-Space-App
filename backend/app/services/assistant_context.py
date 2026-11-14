"""HTTP-independent bridge from canonical snapshots to the deterministic assistant."""
from app.services.assistant_response import respond_to_request
from app.services.snapshot_context import resolve_context


def answer_request(db, request):
    body = request.model_dump()
    context = resolve_context(
        db, farm_id=body["farm_id"], analysis_id=body["analysis_id"],
        scenario_id=body["scenario_id"], candidate_id=body["candidate_id"],
    )
    return respond_to_request(body, context)
