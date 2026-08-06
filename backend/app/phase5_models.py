from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class CommercialDeal(Base):
    __tablename__ = "commercial_deals"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    supplier_match_id: Mapped[int] = mapped_column(
        ForeignKey("supplier_buyer_matches.id"), unique=True, index=True
    )
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"), index=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("buyers.id"), index=True)
    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id"), nullable=True, unique=True, index=True
    )
    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey("invoices.id"), nullable=True, unique=True, index=True
    )
    dispatch_id: Mapped[int | None] = mapped_column(
        ForeignKey("dispatches.id"), nullable=True, unique=True, index=True
    )
    supplier_payment_id: Mapped[int | None] = mapped_column(
        ForeignKey("supplier_payments.id"), nullable=True, unique=True
    )
    status: Mapped[str] = mapped_column(
        String(60), default="Draft quotation", index=True
    )
    product_description: Mapped[str] = mapped_column(Text)
    quantity: Mapped[str] = mapped_column(String(120))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    supplier_unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    delivery_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    transaction_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    service_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    supplier_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    gross_margin: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    payment_status: Mapped[str] = mapped_column(
        String(40), default="Unpaid", index=True
    )
    fulfilment_status: Mapped[str] = mapped_column(
        String(60), default="Not started", index=True
    )
    quality_status: Mapped[str] = mapped_column(
        String(60), default="Not inspected", index=True
    )
    buyer_acceptance_status: Mapped[str] = mapped_column(
        String(40), default="Pending", index=True
    )
    supplier_acceptance_status: Mapped[str] = mapped_column(
        String(40), default="Pending", index=True
    )
    terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class DealTimelineEvent(Base):
    __tablename__ = "deal_timeline_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    deal_id: Mapped[int] = mapped_column(
        ForeignKey("commercial_deals.id"), index=True
    )
    event_type: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(180))
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
