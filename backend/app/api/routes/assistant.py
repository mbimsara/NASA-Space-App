"""Read-only assistant HTTP boundary; no AI provider or NASA calls."""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.routes.rotations import error
from app.database.connection import get_db
from app.schemas.assistant import AssistantRequest, AssistantResponse
from app.services.assistant_context import AssistantContextError, explain_context, resolve_context

router = APIRouter(tags=["Assistant"])


@router.post("/assistant/messages", response_model=AssistantResponse)
def assistant_message(request: AssistantRequest, response: Response, db: Session = Depends(get_db)):
    try:
        context = resolve_context(db, request)
        db.rollback()
        result = AssistantResponse.model_validate(explain_context(context, request))
        response.headers["Cache-Control"] = "no-store"
        return result
    except AssistantContextError as exc:
        db.rollback()
        return error(exc.status, exc.code, str(exc))
    except (SQLAlchemyError, ValueError, TypeError, KeyError, IndexError):
        db.rollback()
        return error(503, "SERVICE_UNAVAILABLE", "Assistant context or explanation service is unavailable.")
