from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base
from .models import StoredDocument, User


class EntrepreneurWorkspace(Base):
    __tablename__ = "entrepreneur_workspaces"

    id: Mapped[int] = mapped_column(primary_key=True)
    entrepreneur_id: Mapped[int] = mapped_column(
        ForeignKey("entrepreneurship_applications.id"),
        unique=True,
        index=True,
    )
    business_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    business_stage: Mapped[str] = mapped_column(String(80), default="Idea stage")
    commercial_status: Mapped[str] = mapped_column(String(80), default="Not started")
    mentorship_status: Mapped[str] = mapped_column(String(80), default="Unassigned")
    funding_status: Mapped[str] = mapped_column(String(80), default="Not started")
    launch_status: Mapped[str] = mapped_column(String(80), default="Not started")
    marketplace_status: Mapped[str] = mapped_column(String(80), default="Not ready")
    supplier_verification_status: Mapped[str] = mapped_column(
        String(80), default="Not verified"
    )
    next_action: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_launch_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    monthly_turnover: Mapped[int | None] = mapped_column(Integer, nullable=True)
    employees_count: Mapped[int] = mapped_column(Integer, default=0)
    production_started: Mapped[bool] = mapped_column(Boolean, default=False)
    first_sale_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_mentor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    assigned_mentor: Mapped[User | None] = relationship(
        foreign_keys=[assigned_mentor_id]
    )


class EntrepreneurTask(Base):
    __tablename__ = "entrepreneur_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    entrepreneur_id: Mapped[int] = mapped_column(
        ForeignKey("entrepreneurship_applications.id"), index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(80), default="Business")
    priority: Mapped[str] = mapped_column(String(30), default="Medium")
    status: Mapped[str] = mapped_column(String(40), default="Not started")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    assigned_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class MentorSession(Base):
    __tablename__ = "mentor_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    entrepreneur_id: Mapped[int] = mapped_column(
        ForeignKey("entrepreneurship_applications.id"), index=True
    )
    mentor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    session_date: Mapped[datetime] = mapped_column(DateTime)
    session_type: Mapped[str] = mapped_column(String(80), default="Progress review")
    status: Mapped[str] = mapped_column(String(40), default="Scheduled")
    objectives: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    actions: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )


class DocumentReview(Base):
    __tablename__ = "document_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("stored_documents.id"), unique=True, index=True
    )
    review_status: Mapped[str] = mapped_column(String(40), default="Pending review")
    reviewer_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    document: Mapped[StoredDocument] = relationship()
