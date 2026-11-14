"""Append-only saved plans referencing main's canonical snapshot tables."""
from sqlalchemy import Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class SavedPlanSnapshot(Base):
    __tablename__ = "saved_plan_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.id"), index=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("rotation_analysis_snapshots.id"))
    scenario_id: Mapped[str | None] = mapped_column(ForeignKey("rotation_scenario_snapshots.id"), nullable=True)
    observation_id: Mapped[str] = mapped_column(ForeignKey("observation_snapshots.id"))
    candidate_id: Mapped[str] = mapped_column(String(200))
    input_version: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[float] = mapped_column(Float)
    payload: Mapped[dict] = mapped_column(JSON)
