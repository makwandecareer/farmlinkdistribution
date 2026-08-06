from __future__ import annotations

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class SupplierActivationUpdate(BaseModel):
    activation_status: str | None = Field(default=None, max_length=60)
    verification_status: str | None = Field(default=None, max_length=60)
    verification_notes: str | None = Field(default=None, max_length=5000)
    marketplace_enabled: bool | None = None
    buyer_matching_enabled: bool | None = None


class FarmerConversionCreate(BaseModel):
    farm_name: str = Field(min_length=2, max_length=200)
    location: str = Field(min_length=2, max_length=255)
    producer_type: str = Field(min_length=2, max_length=100)
    weekly_capacity: int = Field(ge=0)
    egg_sizes: str = Field(min_length=1, max_length=255)
    packaging: str | None = Field(default=None, max_length=255)
    delivery_capability: str = Field(min_length=2, max_length=120)
    notes: str | None = Field(default=None, max_length=5000)


class BuyerRequirementCreate(BaseModel):
    buyer_id: int = Field(gt=0)
    product_category: str = Field(min_length=2, max_length=160)
    product_description: str = Field(min_length=2, max_length=5000)
    location: str = Field(min_length=2, max_length=255)
    quantity_required: str = Field(min_length=1, max_length=120)
    minimum_weekly_capacity: int = Field(default=0, ge=0)
    packaging_required: str | None = Field(default=None, max_length=255)
    quality_requirements: str | None = Field(default=None, max_length=5000)
    delivery_required: bool = False
    frequency: str = Field(default="Once-off", max_length=100)
    required_from: date | None = None
    required_until: date | None = None
    status: str = Field(default="Open", max_length=40)


class BuyerRequirementUpdate(BaseModel):
    product_category: str | None = Field(default=None, max_length=160)
    product_description: str | None = Field(default=None, max_length=5000)
    location: str | None = Field(default=None, max_length=255)
    quantity_required: str | None = Field(default=None, max_length=120)
    minimum_weekly_capacity: int | None = Field(default=None, ge=0)
    packaging_required: str | None = Field(default=None, max_length=255)
    quality_requirements: str | None = Field(default=None, max_length=5000)
    delivery_required: bool | None = None
    frequency: str | None = Field(default=None, max_length=100)
    required_from: date | None = None
    required_until: date | None = None
    status: str | None = Field(default=None, max_length=40)


class MatchUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=50)
    introduction_notes: str | None = Field(default=None, max_length=5000)
    outcome: str | None = Field(default=None, max_length=100)


class MarketplaceListingCreate(BaseModel):
    entrepreneur_id: int = Field(gt=0)
    product_name: str = Field(min_length=2, max_length=180)
    product_category: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=10, max_length=5000)
    location: str = Field(min_length=2, max_length=255)
    weekly_capacity: int = Field(default=0, ge=0)
    packaging: str | None = Field(default=None, max_length=255)
    delivery_capability: str = Field(min_length=2, max_length=120)
    minimum_order: str | None = Field(default=None, max_length=120)
    unit_price: Decimal | None = Field(default=None, ge=0)
    contact_visible: bool = False
    featured: bool = False
    status: str = Field(default="Draft", max_length=40)


class MarketplaceListingUpdate(BaseModel):
    product_name: str | None = Field(default=None, max_length=180)
    product_category: str | None = Field(default=None, max_length=160)
    description: str | None = Field(default=None, max_length=5000)
    location: str | None = Field(default=None, max_length=255)
    weekly_capacity: int | None = Field(default=None, ge=0)
    packaging: str | None = Field(default=None, max_length=255)
    delivery_capability: str | None = Field(default=None, max_length=120)
    minimum_order: str | None = Field(default=None, max_length=120)
    unit_price: Decimal | None = Field(default=None, ge=0)
    contact_visible: bool | None = None
    featured: bool | None = None
    status: str | None = Field(default=None, max_length=40)
