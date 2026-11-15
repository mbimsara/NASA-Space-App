"""HTTP-independent bridge from canonical snapshots to the deterministic assistant."""
from app.services.assistant_response import respond_to_request
from app.services.assistant_llm import enhance
from app.services.snapshot_context import resolve_context


def answer_request(db, request):
    body = request.model_dump()
    context = resolve_context(
        db, farm_id=body["farm_id"], analysis_id=body["analysis_id"],
        scenario_id=body["scenario_id"], candidate_id=body["candidate_id"],
    )
    response = respond_to_request(body, context)
    # Selection-level disclosures belong at the HTTP integration boundary.
    # Keep Akash's focused rendering/citation logic unchanged: a farm-only
    # question may not render the selected scenario or observation sections.
    disclosures = []
    if any(context[key].get("data_kind") == "synthetic" for key in
           ("profile", "analysis", "observations", "scenario") if key in context):
        disclosures.append("Selected context includes synthetic demonstration inputs; those inputs are not actual NASA observations or validated agronomic advice.")
    if "scenario" in context:
        disclosures.append("The selected scenario is hypothetical, not a weather forecast or a new NASA observation.")
    response["limitations"] = list(dict.fromkeys([*response["limitations"], *disclosures]))
    return enhance(body, response)
