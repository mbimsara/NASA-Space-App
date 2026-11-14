"""Immutable crop-rotation analyses and their exact input/result snapshot."""

from sqlalchemy import Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class RotationAnalysisSnapshot(Base):
    __tablename__ = "rotation_analysis_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    input_version: Mapped[int] = mapped_column(Integer, nullable=False)
    observation_id: Mapped[str] = mapped_column(
        ForeignKey("observation_snapshots.id"), nullable=False, index=True,
    )
    created_at: Mapped[float] = mapped_column(Float, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
