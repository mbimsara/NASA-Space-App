"""Append-only analyses with original inputs and engine/catalog provenance."""
from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class RotationAnalysis(Base):
    __tablename__ = "rotation_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.id"), index=True)
    input_version: Mapped[int] = mapped_column(Integer)
    observation_id: Mapped[str] = mapped_column(ForeignKey("observation_snapshots.id"))
    inputs: Mapped[dict] = mapped_column(JSON)
    payload: Mapped[dict] = mapped_column(JSON)
