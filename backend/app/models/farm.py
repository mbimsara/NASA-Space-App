
from uuid import uuid4

from sqlalchemy import Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4())
    )

    input_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
    )

    profile: Mapped[dict] = mapped_column(
        JSON,
        nullable=False
    )
