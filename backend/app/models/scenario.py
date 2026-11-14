"""Append-only hypothetical results linked to their immutable baseline."""
from sqlalchemy import ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class ClimateScenario(Base):
    __tablename__ = "climate_scenarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    baseline_analysis_id: Mapped[str] = mapped_column(
        ForeignKey("rotation_analyses.id"), nullable=False, index=True,
    )
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False)
    inputs: Mapped[dict] = mapped_column(JSON, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
