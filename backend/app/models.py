from __future__ import annotations
from datetime import datetime, date
from enum import Enum
from sqlalchemy import String, Text, DateTime, Date, Integer, Boolean, ForeignKey, Numeric, JSON, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class UserRole(str, Enum):
    CEO = "CEO"
    ADMIN = "ADMIN"
    FINANCE = "FINANCE"
    OPERATIONS = "OPERATIONS"
    LOGISTICS = "LOGISTICS"
    QUALITY = "QUALITY"
    FARMER = "FARMER"
    BUYER = "BUYER"

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

class InventoryLot(Base):
    __tablename__ = "inventory_lots"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"), index=True)
    egg_size: Mapped[str] = mapped_column(String(60))
    packaging: Mapped[str] = mapped_column(String(100))
    trays_available: Mapped[int] = mapped_column(Integer, default=0)
    unit_price: Mapped[float | None] = mapped_column(Numeric(12,2), nullable=True)
    available_from: Mapped[date] = mapped_column(Date, default=date.today)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="Available")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    farmer: Mapped[Farmer] = relationship()

class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[int] = mapped_column(primary_key=True)
    registration: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    vehicle_type: Mapped[str] = mapped_column(String(80))
    capacity_trays: Mapped[int] = mapped_column(Integer, default=0)
    driver_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    driver_phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="Available")
    next_service_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Dispatch(Base):
    __tablename__ = "dispatches"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True)
    driver_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    collection_location: Mapped[str] = mapped_column(String(255))
    delivery_location: Mapped[str] = mapped_column(String(255))
    scheduled_date: Mapped[datetime] = mapped_column(DateTime)
    dispatched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    trays: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="Scheduled")
    tracking_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    order: Mapped[Order] = relationship()
    vehicle: Mapped[Vehicle | None] = relationship()

class QualityCase(Base):
    __tablename__ = "quality_cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    farmer_id: Mapped[int | None] = mapped_column(ForeignKey("farmers.id"), nullable=True)
    case_type: Mapped[str] = mapped_column(String(100))
    trays_affected: Mapped[int] = mapped_column(Integer, default=0)
    severity: Mapped[str] = mapped_column(String(30), default="Medium")
    status: Mapped[str] = mapped_column(String(30), default="Open")
    findings: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrective_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[int] = mapped_column(Integer)
    customer_name: Mapped[str] = mapped_column(String(200))
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    subtotal: Mapped[float] = mapped_column(Numeric(12,2))
    tax_amount: Mapped[float] = mapped_column(Numeric(12,2), default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(12,2))
    amount_paid: Mapped[float] = mapped_column(Numeric(12,2), default=0)
    status: Mapped[str] = mapped_column(String(30), default="Unpaid")
    due_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class SupplierPayment(Base):
    __tablename__ = "supplier_payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("farmers.id"), index=True)
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(12,2))
    method: Mapped[str] = mapped_column(String(80), default="EFT")
    bank_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="Pending")
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    farmer: Mapped[Farmer] = relationship()

class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(40), default="Paystack")
    entity_type: Mapped[str] = mapped_column(String(40))
    entity_id: Mapped[int] = mapped_column(Integer)
    payer_email: Mapped[str] = mapped_column(String(255))
    amount: Mapped[float] = mapped_column(Numeric(12,2))
    currency: Mapped[str] = mapped_column(String(10), default="ZAR")
    status: Mapped[str] = mapped_column(String(30), default="Initialized")
    authorization_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    provider_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class RefundRecord(Base):
    __tablename__ = "refund_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True)
    payment_transaction_id: Mapped[int] = mapped_column(ForeignKey("payment_transactions.id"))
    amount: Mapped[float] = mapped_column(Numeric(12,2))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="Requested")
    provider_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class StoredDocument(Base):
    __tablename__ = "stored_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(40), index=True)
    entity_id: Mapped[int] = mapped_column(Integer, index=True)
    document_type: Mapped[str] = mapped_column(String(80))
    filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    file_size: Mapped[int] = mapped_column(Integer)
    file_data: Mapped[bytes] = mapped_column(LargeBinary)
    uploaded_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    channel: Mapped[str] = mapped_column(String(30))
    recipient: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="Queued")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    successful: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

# FarmLink AgriStart module
from datetime import datetime as _agristart_datetime
from sqlalchemy import Column as _ASColumn, Integer as _ASInteger, String as _ASString, Text as _ASText, DateTime as _ASDateTime, ForeignKey as _ASForeignKey

class EntrepreneurshipApplication(Base):
    __tablename__ = "entrepreneurship_applications"

    id = _ASColumn(_ASInteger, primary_key=True)
    reference = _ASColumn(_ASString(50), unique=True, index=True, nullable=False)
    full_name = _ASColumn(_ASString(200), nullable=False)
    phone = _ASColumn(_ASString(50), nullable=False)
    email = _ASColumn(_ASString(255), nullable=False)
    province = _ASColumn(_ASString(100), nullable=False)
    municipality = _ASColumn(_ASString(150), nullable=False)
    institution = _ASColumn(_ASString(200), nullable=False)
    qualification = _ASColumn(_ASString(200), nullable=False)
    study_status = _ASColumn(_ASString(100), nullable=False)
    agricultural_interest = _ASColumn(_ASString(150), nullable=False)
    current_resources = _ASColumn(_ASText, nullable=True)
    support_required = _ASColumn(_ASText, nullable=True)
    business_idea = _ASColumn(_ASText, nullable=False)
    status = _ASColumn(_ASString(100), nullable=False, default="New")
    assigned_to_id = _ASColumn(_ASInteger, _ASForeignKey("users.id"), nullable=True)
    internal_notes = _ASColumn(_ASText, nullable=True)
    created_at = _ASColumn(_ASDateTime, nullable=False, default=_agristart_datetime.utcnow)
    updated_at = _ASColumn(_ASDateTime, nullable=False, default=_agristart_datetime.utcnow, onupdate=_agristart_datetime.utcnow)