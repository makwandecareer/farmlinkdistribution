from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base
from .models import User


class FundingServiceApplication(Base):
    __tablename__ = "funding_service_applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)

    entrepreneur_application_id: Mapped[int | None] = mapped_column(
        ForeignKey("entrepreneurship_applications.id"), nullable=True, index=True
    )
    agristart_reference: Mapped[str | None] = mapped_column(String(60), nullable=True, index=True)

    applicant_name: Mapped[str] = mapped_column(String(180), index=True)
    business_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[str] = mapped_column(String(50), index=True)
    province: Mapped[str] = mapped_column(String(100), index=True)
    municipality: Mapped[str | None] = mapped_column(String(180), nullable=True)
    agricultural_interest: Mapped[str | None] = mapped_column(String(180), nullable=True)
    business_idea: Mapped[str | None] = mapped_column(Text, nullable=True)

    service_code: Mapped[str] = mapped_column(String(60), index=True)
    service_name: Mapped[str] = mapped_column(String(180))
    service_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    service_status: Mapped[str] = mapped_column(
        String(80), default="Application received", index=True
    )

    payment_status: Mapped[str] = mapped_column(
        String(80), default="Not invoiced", index=True
    )
    payment_method: Mapped[str | None] = mapped_column(String(80), nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    funding_status: Mapped[str] = mapped_column(
        String(80), default="Not started", index=True
    )
    funding_amount_required: Mapped[Decimal | None] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    funding_purpose: Mapped[str | None] = mapped_column(String(255), nullable=True)
    funder_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    funder_contact: Mapped[str | None] = mapped_column(String(180), nullable=True)
    funder_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    funder_application_reference: Mapped[str | None] = mapped_column(
        String(120), nullable=True
    )
    submission_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    decision_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    outstanding_documents: Mapped[str | None] = mapped_column(Text, nullable=True)

    business_plan: Mapped[bool] = mapped_column(Boolean, default=False)
    cash_flow: Mapped[bool] = mapped_column(Boolean, default=False)
    pitch_deck: Mapped[bool] = mapped_column(Boolean, default=False)
    company_registration: Mapped[bool] = mapped_column(Boolean, default=False)
    tax_status: Mapped[bool] = mapped_column(Boolean, default=False)
    bank_account: Mapped[bool] = mapped_column(Boolean, default=False)

    launch_status: Mapped[str] = mapped_column(
        String(80), default="Not started", index=True
    )
    launch_readiness_score: Mapped[int] = mapped_column(Integer, default=0)
    next_action: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_launch_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    assigned_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    consent_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    terms_accepted: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    assigned_to: Mapped[User | None] = relationship(foreign_keys=[assigned_to_id])
