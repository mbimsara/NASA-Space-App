from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.database.connection import Base, get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "AgroSphere AI backend is running"
    }


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Local DB readiness only; does not call NASA or reveal DB details."""
    try:
        db.execute(text("SELECT 1"))
        existing = set(inspect(db.connection()).get_table_names())
        if not set(Base.metadata.tables).issubset(existing):
            raise ValueError("Schema unavailable")
    except (SQLAlchemyError, ValueError):
        return JSONResponse(status_code=503, content={"error": {
            "code": "SERVICE_UNAVAILABLE", "message": "Database is not ready.",
        }})
    return {"status": "ready"}
