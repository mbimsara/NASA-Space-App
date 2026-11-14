"""Immutable hypothetical climate scenarios derived from a saved rotation analysis."""

from sqlalchemy import Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class RotationScenarioSnapshot(Base):
    __tablename__ = "rotation_scenario_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    analysis_id: Mapped[str] = mapped_column(
        ForeignKey("rotation_analysis_snapshots.id"), nullable=False, index=True,
    )
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    input_version: Mapped[int] = mapped_column(Integer, nullable=False)
    observation_id: Mapped[str] = mapped_column(
        ForeignKey("observation_snapshots.id"), nullable=False, index=True,
    )
    rainfall_change_pct: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[float] = mapped_column(Float, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
