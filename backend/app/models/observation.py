"""Append-only observation responses and the farm inputs used to retrieve them."""

from sqlalchemy import Float, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class ObservationSnapshot(Base):
    __tablename__ = "observation_snapshots"
    __table_args__ = (
        UniqueConstraint("cache_key", "generation", name="uq_observation_cache_generation"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    cache_key: Mapped[str] = mapped_column(String(64), nullable=False)
    generation: Mapped[int] = mapped_column(Integer, nullable=False)
    farm_id: Mapped[str] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    input_version: Mapped[int] = mapped_column(Integer, nullable=False)
    farm_profile: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Epoch seconds avoid SQLite's loss of timezone information in DateTime columns.
    cached_at: Mapped[float] = mapped_column(Float, nullable=False)
    expires_at: Mapped[float] = mapped_column(Float, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
