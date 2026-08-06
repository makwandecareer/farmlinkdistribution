from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class SupplierActivationProfile(Base):
    __tablename__ = "supplier_activation_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    entrepreneur_id: Mapped[int] = mapped_column(
        ForeignKey("entrepreneurship_applications.id"),
        unique=True,
        index=True,
    )
    farmer_id: Mapped[int | None] = mapped_column(
        ForeignKey("farmers.id"), nullable=True, unique=True, index=True
    )
    activation_status: Mapped[str] = mapped_column(
        String(60), default="Not started", index=True
    )
    verification_status: Mapped[str] = mapped_column(
        String(60), default="Not verified", index=True
    )
    verification_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    marketplace_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    buyer_matching_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class BuyerRequirement(Base):
    __tablename__ = "buyer_requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("buyers.id"), index=True)
    product_category: Mapped[str] = mapped_column(String(160), index=True)
    product_description: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(255), index=True)
    quantity_required: Mapped[str] = mapped_column(String(120))
    minimum_weekly_capacity: Mapped[int] = mapped_column(Integer, default=0)
    packaging_required: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quality_requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    delivery_required: Mapped[bool] = mapped_column(Boolean, default=False)
    frequency: Mapped[str] = mapped_column(String(100), default="Once-off")
    required_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    required_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="Open", index=True)
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class SupplierBuyerMatch(Base):
    __tablename__ = "supplier_buyer_matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    entrepreneur_id: Mapped[int] = mapped_column(
        ForeignKey("entrepreneurship_applications.id"), index=True
    )
    farmer_id: Mapped[int | None] = mapped_column(
        ForeignKey("farmers.id"), nullable=True, index=True
    )
    buyer_requirement_id: Mapped[int] = mapped_column(
        ForeignKey("buyer_requirements.id"), index=True
    )
    match_score: Mapped[int] = mapped_column(Integer, default=0, index=True)
    product_score: Mapped[int] = mapped_column(Integer, default=0)
    location_score: Mapped[int] = mapped_column(Integer, default=0)
    capacity_score: Mapped[int] = mapped_column(Integer, default=0)
    packaging_score: Mapped[int] = mapped_column(Integer, default=0)
    delivery_score: Mapped[int] = mapped_column(Integer, default=0)
    match_reasons: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="Suggested", index=True)
    introduction_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    introduced_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    entrepreneur_id: Mapped[int] = mapped_column(
        ForeignKey("entrepreneurship_applications.id"), index=True
    )
    farmer_id: Mapped[int | None] = mapped_column(
        ForeignKey("farmers.id"), nullable=True, index=True
    )
    business_name: Mapped[str] = mapped_column(String(200), index=True)
    product_name: Mapped[str] = mapped_column(String(180), index=True)
    product_category: Mapped[str] = mapped_column(String(160), index=True)
    description: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(255), index=True)
    weekly_capacity: Mapped[int] = mapped_column(Integer, default=0)
    packaging: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delivery_capability: Mapped[str] = mapped_column(String(120))
    minimum_order: Mapped[str | None] = mapped_column(String(120), nullable=True)
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    contact_visible: Mapped[bool] = mapped_column(Boolean, default=False)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(40), default="Draft", index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
