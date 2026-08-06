from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator


BUSINESS_STAGES = [
    "Idea stage",
    "Validation",
    "Business planning",
    "Funding readiness",
    "Pre-launch",
    "Operating",
    "Growth",
]

WORKSPACE_STATUSES = [
    "Not started",
    "In progress",
    "At risk",
    "Ready",
    "Completed",
]

DOCUMENT_TYPES = [
    "ID Document",
    "CIPC Registration",
    "Tax Compliance",
    "B-BBEE Affidavit",
    "Bank Confirmation Letter",
    "Business Plan",
    "Cash-flow Projection",
    "Pitch Deck",
    "Company Profile",
    "Proof of Address",
    "Supplier Quotation",
    "Funding Application",
    "Financial Statements",
]

DOCUMENT_REVIEW_STATUSES = [
    "Pending review",
    "Approved",
    "Correction required",
    "Rejected",
]


class WorkspaceUpdate(BaseModel):
    business_name: str | None = Field(default=None, max_length=200)
    business_stage: str | None = None
    commercial_status: str | None = None
    mentorship_status: str | None = None
    funding_status: str | None = None
    launch_status: str | None = None
    marketplace_status: str | None = None
    supplier_verification_status: str | None = None
    next_action: str | None = Field(default=None, max_length=255)
    target_launch_date: date | None = None
    monthly_turnover: int | None = Field(default=None, ge=0)
    employees_count: int | None = Field(default=None, ge=0)
    production_started: bool | None = None
    first_sale_completed: bool | None = None
    internal_notes: str | None = Field(default=None, max_length=10000)
    assigned_mentor_id: int | None = None

    @field_validator("business_stage")
    @classmethod
    def stage_valid(cls, value: str | None) -> str | None:
        if value is not None and value not in BUSINESS_STAGES:
            raise ValueError("Invalid business stage")
        return value


class TaskCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    category: str = Field(default="Business", max_length=80)
    priority: str = Field(default="Medium", max_length=30)
    status: str = Field(default="Not started", max_length=40)
    due_date: date | None = None
    assigned_to_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    category: str | None = Field(default=None, max_length=80)
    priority: str | None = Field(default=None, max_length=30)
    status: str | None = Field(default=None, max_length=40)
    due_date: date | None = None
    assigned_to_id: int | None = None


class MentorSessionCreate(BaseModel):
    mentor_id: int | None = None
    session_date: datetime
    session_type: str = Field(default="Progress review", max_length=80)
    status: str = Field(default="Scheduled", max_length=40)
    objectives: str | None = Field(default=None, max_length=5000)
    notes: str | None = Field(default=None, max_length=10000)
    actions: str | None = Field(default=None, max_length=5000)
    score: int | None = Field(default=None, ge=0, le=100)


class MentorSessionUpdate(BaseModel):
    mentor_id: int | None = None
    session_date: datetime | None = None
    session_type: str | None = Field(default=None, max_length=80)
    status: str | None = Field(default=None, max_length=40)
    objectives: str | None = Field(default=None, max_length=5000)
    notes: str | None = Field(default=None, max_length=10000)
    actions: str | None = Field(default=None, max_length=5000)
    score: int | None = Field(default=None, ge=0, le=100)


class DocumentReviewUpdate(BaseModel):
    review_status: str
    reviewer_comment: str | None = Field(default=None, max_length=5000)

    @field_validator("review_status")
    @classmethod
    def review_valid(cls, value: str) -> str:
        if value not in DOCUMENT_REVIEW_STATUSES:
            raise ValueError("Invalid document review status")
        return value


class PublicWorkspaceAccess(BaseModel):
    reference: str = Field(min_length=5, max_length=60)
    email: str = Field(min_length=5, max_length=255)
