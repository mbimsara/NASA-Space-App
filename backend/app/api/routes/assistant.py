"""Grounded assistant API; never calls an AI or weather provider."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.assistant import AssistantRequest, AssistantResponse
from app.services.assistant_context import answer_request
from app.services.assistant_errors import UnsupportedLanguageError
from app.services.snapshot_context import SelectionError

router = APIRouter(tags=["Assistant"])


def error(status, code, message):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}},
                        headers={"Cache-Control": "no-store"})


@router.post("/assistant/messages", response_model=AssistantResponse)
def assistant_message(request: AssistantRequest, db: Session = Depends(get_db)):
    try:
        return JSONResponse(content=AssistantResponse.model_validate(
            answer_request(db, request)).model_dump(mode="json"), headers={"Cache-Control": "no-store"})
    except UnsupportedLanguageError:
        return error(422, "UNSUPPORTED_LANGUAGE", "Only English is supported until translations are reviewed.")
    except SelectionError as exc:
        return error(exc.status, exc.code, exc.message)
    except (SQLAlchemyError, ValueError, TypeError, KeyError):
        db.rollback()
        return error(503, "SERVICE_UNAVAILABLE", "The stored assistant context is unavailable or inconsistent.")
