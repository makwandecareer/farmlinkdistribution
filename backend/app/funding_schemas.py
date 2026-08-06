from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


SERVICE_CATALOG = {
    "readiness_assessment": {
        "name": "Funding Readiness Assessment",
        "fee": Decimal("499.00"),
    },
    "application_support": {
        "name": "Funding Application Support",
        "fee": Decimal("999.00"),
    },
    "full_funding_pack": {
        "name": "Full Funding Pack",
        "fee": Decimal("1999.00"),
    },
}

SERVICE_STATUSES = [
    "Application received",
    "Assessment scheduled",
    "Assessment in progress",
    "Documents required",
    "Ready to commence",
    "Work in progress",
    "Completed",
    "Cancelled",
]

PAYMENT_STATUSES = [
    "Not invoiced",
    "Invoice issued",
    "Awaiting payment",
    "Part paid",
    "Paid",
    "Failed",
    "Refunded",
    "Cancelled",
]

FUNDING_STATUSES = [
    "Not started",
    "Documents required",
    "Funding ready",
    "Application submitted",
    "Under review",
    "Approved",
    "Declined",
]

LAUNCH_STATUSES = [
    "Not started",
    "In progress",
    "At risk",
    "Launch ready",
    "Launched",
]


class FundingServiceCreate(BaseModel):
    applicant_name: str = Field(min_length=2, max_length=180)
    business_name: str | None = Field(default=None, max_length=180)
    email: EmailStr
    phone: str = Field(min_length=7, max_length=50)
    province: str = Field(min_length=2, max_length=100)
    municipality: str | None = Field(default=None, max_length=180)
    agricultural_interest: str | None = Field(default=None, max_length=180)
    business_idea: str | None = Field(default=None, max_length=5000)
    agristart_reference: str | None = Field(default=None, max_length=60)
    entrepreneur_application_id: int | None = Field(default=None, gt=0)
    service_code: Literal[
        "readiness_assessment",
        "application_support",
        "full_funding_pack",
    ]
    funding_amount_required: Decimal | None = Field(default=None, ge=0)
    funding_purpose: str | None = Field(default=None, max_length=255)
    consent_confirmed: bool
    terms_accepted: bool

    @field_validator("consent_confirmed", "terms_accepted")
    @classmethod
    def accepted(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Consent and service terms must be accepted")
        return value


class FundingServiceUpdate(BaseModel):
    entrepreneur_application_id: int | None = None
    agristart_reference: str | None = Field(default=None, max_length=60)
    applicant_name: str | None = Field(default=None, min_length=2, max_length=180)
    business_name: str | None = Field(default=None, max_length=180)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    province: str | None = Field(default=None, max_length=100)
    municipality: str | None = Field(default=None, max_length=180)
    agricultural_interest: str | None = Field(default=None, max_length=180)
    business_idea: str | None = Field(default=None, max_length=5000)

    service_code: Literal[
        "readiness_assessment",
        "application_support",
        "full_funding_pack",
    ] | None = None
    service_status: str | None = None

    payment_status: str | None = None
    payment_method: str | None = Field(default=None, max_length=80)
    payment_reference: str | None = Field(default=None, max_length=120)
    payment_date: date | None = None

    funding_status: str | None = None
    funding_amount_required: Decimal | None = Field(default=None, ge=0)
    funding_purpose: str | None = Field(default=None, max_length=255)
    funder_name: str | None = Field(default=None, max_length=180)
    funder_contact: str | None = Field(default=None, max_length=180)
    funder_email: EmailStr | None = None
    funder_application_reference: str | None = Field(default=None, max_length=120)
    submission_date: date | None = None
    decision_date: date | None = None
    follow_up_date: date | None = None
    outstanding_documents: str | None = None

    business_plan: bool | None = None
    cash_flow: bool | None = None
    pitch_deck: bool | None = None
    company_registration: bool | None = None
    tax_status: bool | None = None
    bank_account: bool | None = None

    launch_status: str | None = None
    launch_readiness_score: int | None = Field(default=None, ge=0, le=100)
    next_action: str | None = Field(default=None, max_length=255)
    target_launch_date: date | None = None

    assigned_to_id: int | None = None
    internal_notes: str | None = Field(default=None, max_length=10000)

    @field_validator("service_status")
    @classmethod
    def service_status_valid(cls, value: str | None) -> str | None:
        if value is not None and value not in SERVICE_STATUSES:
            raise ValueError("Invalid service status")
        return value

    @field_validator("payment_status")
    @classmethod
    def payment_status_valid(cls, value: str | None) -> str | None:
        if value is not None and value not in PAYMENT_STATUSES:
            raise ValueError("Invalid payment status")
        return value

    @field_validator("funding_status")
    @classmethod
    def funding_status_valid(cls, value: str | None) -> str | None:
        if value is not None and value not in FUNDING_STATUSES:
            raise ValueError("Invalid funding status")
        return value

    @field_validator("launch_status")
    @classmethod
    def launch_status_valid(cls, value: str | None) -> str | None:
        if value is not None and value not in LAUNCH_STATUSES:
            raise ValueError("Invalid launch status")
        return value
