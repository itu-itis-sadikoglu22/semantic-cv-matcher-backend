from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Job(Base):
    """
    SQLAlchemy model for storing job posting information.
    """

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    seniority: Mapped[str | None] = mapped_column(String(100), nullable=True)
    min_years_experience: Mapped[float | None] = mapped_column(Float, nullable=True)