from __future__ import annotations
from datetime import datetime, date
from enum import Enum
from sqlalchemy import String, Text, DateTime, Date, Integer, Boolean, ForeignKey, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class UserRole(str, Enum):
    CEO = "CEO"
    ADMIN = "ADMIN"

class RecordStatus(str, Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IN_PROGRESS = "In progress"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"

class PaymentStatus(str, Enum):
    PENDING = "Pending"
    INVOICED = "Invoiced"
    PART_PAID = "Part paid"
    PAID = "Paid"
    FAILED = "Failed"
    REFUNDED = "Refunded"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(20), default=UserRole.ADMIN.value)
    job_title: Mapped[str] = mapped_column(String(160), default="Administrator")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class Farmer(Base):
    __tablename__ = "farmers"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    farm_name: Mapped[str] = mapped_column(String(200), index=True)
    contact_person: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location: Mapped[str] = mapped_column(String(255))
    producer_type: Mapped[str] = mapped_column(String(100))
    weekly_capacity: Mapped[int] = mapped_column(Integer)
    egg_sizes: Mapped[str] = mapped_column(String(255))
    packaging: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delivery_capability: Mapped[str] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    membership_plan: Mapped[str] = mapped_column(String(120), default="Standard Farmer — Free")
    status: Mapped[str] = mapped_column(String(30), default=RecordStatus.PENDING.value)
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_to: Mapped[User | None] = relationship()

class Buyer(Base):
    __tablename__ = "buyers"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    business_name: Mapped[str] = mapped_column(String(200), index=True)
    contact_person: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str] = mapped_column(String(40))
    email: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(120))
    location: Mapped[str] = mapped_column(String(255))
    weekly_volume: Mapped[str] = mapped_column(String(120))
    egg_size: Mapped[str | None] = mapped_column(String(100), nullable=True)
    packaging: Mapped[str | None] = mapped_column(String(255), nullable=True)
    frequency: Mapped[str] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    membership_plan: Mapped[str] = mapped_column(String(120), default="Standard Buyer — Free")
    status: Mapped[str] = mapped_column(String(30), default=RecordStatus.PENDING.value)
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_to: Mapped[User | None] = relationship()

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    business_name: Mapped[str] = mapped_column(String(200), index=True)
    contact_person: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str] = mapped_column(String(40))
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_type: Mapped[str] = mapped_column(String(120))
    delivery_area: Mapped[str] = mapped_column(String(255))
    egg_size: Mapped[str] = mapped_column(String(100))
    packaging: Mapped[str] = mapped_column(String(120))
    quantity: Mapped[str] = mapped_column(String(120))
    frequency: Mapped[str] = mapped_column(String(100))
    required_date: Mapped[date] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=RecordStatus.PENDING.value)
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    quoted_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_to: Mapped[User | None] = relationship()

class MembershipApplication(Base):
    __tablename__ = "membership_applications"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    applicant_type: Mapped[str] = mapped_column(String(120))
    selected_service: Mapped[str] = mapped_column(String(160))
    business_name: Mapped[str] = mapped_column(String(200))
    contact_person: Mapped[str] = mapped_column(String(160))
    phone: Mapped[str] = mapped_column(String(40))
    email: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255))
    preferred_payment_method: Mapped[str] = mapped_column(String(120))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=RecordStatus.PENDING.value)
    assigned_to_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    internal_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_to: Mapped[User | None] = relationship()

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int] = mapped_column(Integer)
    payer_name: Mapped[str] = mapped_column(String(200))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    method: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default=PaymentStatus.PENDING.value)
    external_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    proof_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    actor_name: Mapped[str] = mapped_column(String(160))
    action: Mapped[str] = mapped_column(String(160))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
