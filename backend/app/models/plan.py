"""Immutable selected-plan snapshots, independent of future computations."""
from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class SavedPlan(Base):
    __tablename__ = "saved_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.id"), index=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("rotation_analyses.id"), index=True)
    scenario_id: Mapped[str | None] = mapped_column(ForeignKey("climate_scenarios.id"), nullable=True)
    observation_id: Mapped[str] = mapped_column(ForeignKey("observation_snapshots.id"))
    candidate_id: Mapped[str] = mapped_column(String(36))
    input_version: Mapped[int] = mapped_column(Integer)
    provenance: Mapped[dict] = mapped_column(JSON)
    payload: Mapped[dict] = mapped_column(JSON)
