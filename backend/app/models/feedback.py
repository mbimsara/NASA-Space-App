"""Append-only farmer-entered season outcomes attached to immutable plans."""

from sqlalchemy import Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class SeasonFeedback(Base):
    __tablename__ = "season_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    plan_id: Mapped[str] = mapped_column(ForeignKey("saved_plan_snapshots.id"), index=True)
    season_index: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[float] = mapped_column(Float)
    payload: Mapped[dict] = mapped_column(JSON)
