from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CV(Base):
    """
    SQLAlchemy model for storing candidate CV information.
    """

    __tablename__ = "cvs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    candidate_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)