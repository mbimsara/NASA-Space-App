"""Create and list append-only farmer-entered plan outcomes."""

from datetime import datetime, timezone
from time import time
from uuid import uuid4

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.feedback import SeasonFeedback
from app.models.plan import SavedPlanSnapshot
from app.schemas.feedback import FeedbackRequest, FeedbackResponse


router = APIRouter(prefix="/plans", tags=["Season feedback"])


def response(row):
    return FeedbackResponse.model_validate(row.payload)


@router.post("/{plan_id}/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_feedback(plan_id: str, request: FeedbackRequest, http: Response, db: Session = Depends(get_db)):
    http.headers["Cache-Control"] = "no-store"
    plan = db.get(SavedPlanSnapshot, plan_id)
    if plan is None:
        return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND", "message": "Saved plan not found."}})
    sequence = plan.payload.get("candidate_snapshot", {}).get("sequence", [])
    if request.season_index not in {item.get("season_index") for item in sequence}:
        return JSONResponse(status_code=422, content={"error": {"code": "INVALID_SEASON", "message": "Season is not present in the saved candidate snapshot."}})
    identifier, created = str(uuid4()), time()
    payload = {"schema_version": "0.1", "feedback_id": identifier, "plan_id": plan_id,
               "data_kind": "farmer_input", "created_at": datetime.fromtimestamp(created, timezone.utc).isoformat(),
               **request.model_dump(mode="json"),
               "limitations": ["Farmer-entered outcome; not independently verified.",
                               "Feedback is stored for review and does not retrain or silently alter the rotation model."]}
    row = SeasonFeedback(id=identifier, plan_id=plan_id, season_index=request.season_index,
                         created_at=created, payload=payload)
    db.add(row); db.commit()
    return response(row)


@router.get("/{plan_id}/feedback", response_model=list[FeedbackResponse])
def list_feedback(plan_id: str, http: Response, db: Session = Depends(get_db)):
    http.headers["Cache-Control"] = "no-store"
    if db.get(SavedPlanSnapshot, plan_id) is None:
        return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND", "message": "Saved plan not found."}})
    rows = db.scalars(select(SeasonFeedback).where(SeasonFeedback.plan_id == plan_id)
                      .order_by(SeasonFeedback.created_at.desc(), SeasonFeedback.id)).all()
    return [response(row) for row in rows]
