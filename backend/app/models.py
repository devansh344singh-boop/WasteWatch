from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def now_utc(): return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="citizen")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    reports: Mapped[list["Report"]] = relationship(back_populates="owner")

class Report(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    category: Mapped[str] = mapped_column(String(40))
    severity: Mapped[str] = mapped_column(String(20), default="Medium")
    description: Mapped[str] = mapped_column(Text)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_path: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(30), default="submitted", index=True)
    predicted_category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_status: Mapped[str] = mapped_column(String(30), default="not_configured")
    requires_human_review: Mapped[bool] = mapped_column(default=True)
    supervisor_remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)
    owner: Mapped[User] = relationship(back_populates="reports")
