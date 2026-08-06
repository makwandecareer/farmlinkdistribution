from datetime import date, datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)

class ChangePasswordIn(BaseModel):
    current_password: str
    new_password: str = Field(min_length=10, max_length=200)

class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    job_title: str = Field(min_length=2, max_length=160)
    role: Literal["ADMIN","FINANCE","OPERATIONS","LOGISTICS","QUALITY"] = "ADMIN"
    temporary_password: str = Field(min_length=10, max_length=200)

class UserUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: EmailStr
    job_title: str = Field(min_length=2, max_length=160)
    role: Literal["ADMIN","FINANCE","OPERATIONS","LOGISTICS","QUALITY","CEO"]

class UserPasswordReset(BaseModel):
    temporary_password: str = Field(min_length=10, max_length=200)

class UserOut(ORMModel):
    id: int; full_name: str; email: EmailStr; role: str; job_title: str; is_active: bool; must_change_password: bool; created_at: datetime; last_login_at: datetime | None

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class FarmerCreate(BaseModel):
    farm_name: str = Field(min_length=2, max_length=200)
    contact_person: str = Field(min_length=2, max_length=160)
    phone: str = Field(min_length=7, max_length=40)
    email: EmailStr | None = None
    location: str = Field(min_length=2, max_length=255)
    producer_type: str
    weekly_capacity: int = Field(ge=1, le=10_000_000)
    egg_sizes: str
    packaging: str | None = None
    delivery_capability: str
    notes: str | None = Field(default=None, max_length=3000)

class BuyerCreate(BaseModel):
    business_name: str; contact_person: str; phone: str; email: EmailStr; category: str; location: str; weekly_volume: str; egg_size: str | None = None; packaging: str | None = None; frequency: str; notes: str | None = None

class OrderCreate(BaseModel):
    business_name: str; contact_person: str; phone: str; email: EmailStr | None = None; customer_type: str; delivery_area: str; egg_size: str; packaging: str; quantity: str; frequency: str; required_date: date; notes: str | None = None
    @field_validator("required_date")
    @classmethod
    def future_date(cls, v: date):
        if v < date.today(): raise ValueError("Required date cannot be in the past")
        return v

class MembershipCreate(BaseModel):
    applicant_type: str; selected_service: str; business_name: str; contact_person: str; phone: str; email: EmailStr; location: str; preferred_payment_method: str; notes: str | None = None

class RecordUpdate(BaseModel):
    status: str | None = None
    assigned_to_id: int | None = None
    internal_notes: str | None = Field(default=None, max_length=5000)
    quoted_amount: float | None = Field(default=None, ge=0)

class PaymentCreate(BaseModel):
    entity_type: Literal["order","membership"]
    entity_id: int
    payer_name: str
    amount: float = Field(gt=0)
    method: str
    status: str = "Pending"
    external_reference: str | None = None
    proof_url: str | None = None
    notes: str | None = None

class PaymentUpdate(BaseModel):
    status: str
    external_reference: str | None = None
    proof_url: str | None = None
    notes: str | None = None

# FarmLink AgriStart module
class EntrepreneurshipCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    phone: str = Field(min_length=7, max_length=50)
    email: EmailStr
    province: str = Field(min_length=2, max_length=100)
    municipality: str = Field(min_length=2, max_length=150)
    institution: str = Field(min_length=2, max_length=200)
    qualification: str = Field(min_length=2, max_length=200)
    study_status: str = Field(min_length=2, max_length=100)
    agricultural_interest: str = Field(min_length=2, max_length=150)
    current_resources: str | None = None
    support_required: str | None = None
    business_idea: str = Field(min_length=20, max_length=5000)