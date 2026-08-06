from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field


class DealCreate(BaseModel):
    supplier_match_id: int = Field(gt=0)
    product_description: str = Field(min_length=2, max_length=5000)
    quantity: str = Field(min_length=1, max_length=120)
    unit_price: Decimal = Field(gt=0)
    supplier_unit_cost: Decimal = Field(ge=0)
    delivery_cost: Decimal = Field(default=0, ge=0)
    transaction_cost: Decimal = Field(default=0, ge=0)
    service_fee: Decimal = Field(default=0, ge=0)
    terms: str | None = Field(default=None, max_length=10000)


class DealUpdate(BaseModel):
    status: str | None = Field(default=None, max_length=60)
    payment_status: str | None = Field(default=None, max_length=40)
    fulfilment_status: str | None = Field(default=None, max_length=60)
    quality_status: str | None = Field(default=None, max_length=60)
    buyer_acceptance_status: str | None = Field(default=None, max_length=40)
    supplier_acceptance_status: str | None = Field(default=None, max_length=40)
    terms: str | None = Field(default=None, max_length=10000)
    internal_notes: str | None = Field(default=None, max_length=10000)


class DealEventCreate(BaseModel):
    event_type: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=2, max_length=180)
    detail: str | None = Field(default=None, max_length=5000)
