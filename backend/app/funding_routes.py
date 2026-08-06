from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from .database import get_db
from .deps import current_user
from .funding_models import FundingServiceApplication
from .funding_schemas import SERVICE_CATALOG, FundingServiceCreate, FundingServiceUpdate
from .models import EntrepreneurshipApplication, User
from .utils import audit, make_reference


router = APIRouter(prefix="/api", tags=["Funding services"])


def readiness_score(record: FundingServiceApplication) -> int:
    flags = [
        record.business_plan,
        record.cash_flow,
        record.pitch_deck,
        record.company_registration,
        record.tax_status,
        record.bank_account,
    ]
    return round(sum(1 for flag in flags if flag) / len(flags) * 100)


def serialize(record: FundingServiceApplication) -> dict:
    result = {
        column.name: getattr(record, column.name)
        for column in record.__table__.columns
    }
    result["service_fee"] = float(record.service_fee)
    result["funding_amount_required"] = (
        float(record.funding_amount_required)
        if record.funding_amount_required is not None
        else None
    )
    result["readiness_score"] = readiness_score(record)
    result["assigned_to"] = (
        {"id": record.assigned_to.id, "full_name": record.assigned_to.full_name}
        if record.assigned_to
        else None
    )
    return result


@router.get("/public/funding-services/options")
def funding_service_options():
    return {
        "services": [
            {"code": code, "name": details["name"], "fee": float(details["fee"])}
            for code, details in SERVICE_CATALOG.items()
        ],
        "disclaimer": (
            "Fees cover professional funding-readiness and application-support "
            "services. Payment does not guarantee funding approval."
        ),
    }


@router.post("/public/funding-services", status_code=201)
def create_funding_service(
    data: FundingServiceCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    agristart = None
    if data.entrepreneur_application_id:
        agristart = db.get(EntrepreneurshipApplication, data.entrepreneur_application_id)
    elif data.agristart_reference:
        agristart = db.scalar(
            select(EntrepreneurshipApplication).where(
                EntrepreneurshipApplication.reference == data.agristart_reference.strip()
            )
        )

    catalog = SERVICE_CATALOG[data.service_code]
    record = FundingServiceApplication(
        reference=make_reference("FND"),
        entrepreneur_application_id=agristart.id if agristart else None,
        agristart_reference=agristart.reference if agristart else data.agristart_reference,
        applicant_name=data.applicant_name.strip(),
        business_name=(data.business_name or "").strip() or None,
        email=str(data.email).lower(),
        phone=data.phone.strip(),
        province=data.province.strip(),
        municipality=(data.municipality or "").strip() or None,
        agricultural_interest=(data.agricultural_interest or "").strip() or None,
        business_idea=(data.business_idea or "").strip() or None,
        service_code=data.service_code,
        service_name=catalog["name"],
        service_fee=catalog["fee"],
        funding_amount_required=data.funding_amount_required,
        funding_purpose=(data.funding_purpose or "").strip() or None,
        consent_confirmed=data.consent_confirmed,
        terms_accepted=data.terms_accepted,
    )
    db.add(record)
    db.flush()
    audit(
        db,
        None,
        "Submitted funding service registration",
        "funding_service",
        record.id,
        {
            "reference": record.reference,
            "service": record.service_name,
            "fee": float(record.service_fee),
            "agristart_reference": record.agristart_reference,
        },
        request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(record)
    return {
        "id": record.id,
        "reference": record.reference,
        "service_name": record.service_name,
        "service_fee": float(record.service_fee),
        "service_status": record.service_status,
        "payment_status": record.payment_status,
    }


@router.get("/admin/funding-services/dashboard")
def funding_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    def count_where(*conditions) -> int:
        statement = select(func.count()).select_from(FundingServiceApplication)
        if conditions:
            statement = statement.where(*conditions)
        return db.scalar(statement) or 0

    revenue = db.scalar(
        select(func.coalesce(func.sum(FundingServiceApplication.service_fee), 0))
        .where(FundingServiceApplication.payment_status == "Paid")
    ) or Decimal("0")

    return {
        "total": count_where(),
        "awaiting_payment": count_where(
            FundingServiceApplication.payment_status.in_(
                ["Not invoiced", "Invoice issued", "Awaiting payment"]
            )
        ),
        "paid": count_where(FundingServiceApplication.payment_status == "Paid"),
        "funding_ready": count_where(
            FundingServiceApplication.funding_status == "Funding ready"
        ),
        "launched": count_where(
            FundingServiceApplication.launch_status == "Launched"
        ),
        "paid_service_revenue": float(revenue),
    }


@router.get("/admin/funding-services")
def list_funding_services(
    q: str | None = None,
    payment_status: str | None = None,
    funding_status: str | None = None,
    launch_status: str | None = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    statement = select(FundingServiceApplication)
    filters = []

    if q:
        search = f"%{q.strip()}%"
        filters.append(
            or_(
                FundingServiceApplication.reference.ilike(search),
                FundingServiceApplication.agristart_reference.ilike(search),
                FundingServiceApplication.applicant_name.ilike(search),
                FundingServiceApplication.business_name.ilike(search),
                FundingServiceApplication.email.ilike(search),
                FundingServiceApplication.phone.ilike(search),
            )
        )
    if payment_status and payment_status != "all":
        filters.append(FundingServiceApplication.payment_status == payment_status)
    if funding_status and funding_status != "all":
        filters.append(FundingServiceApplication.funding_status == funding_status)
    if launch_status and launch_status != "all":
        filters.append(FundingServiceApplication.launch_status == launch_status)

    if filters:
        statement = statement.where(*filters)

    total_statement = select(func.count()).select_from(
        statement.with_only_columns(FundingServiceApplication.id).subquery()
    )
    total = db.scalar(total_statement) or 0
    records = db.scalars(
        statement.order_by(desc(FundingServiceApplication.created_at))
        .offset(offset)
        .limit(limit)
    ).all()
    return {"total": total, "items": [serialize(record) for record in records]}


@router.get("/admin/funding-services/{record_id}")
def funding_service_detail(
    record_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    record = db.get(FundingServiceApplication, record_id)
    if not record:
        raise HTTPException(404, "Funding service registration not found")
    return serialize(record)


@router.patch("/admin/funding-services/{record_id}")
def update_funding_service(
    record_id: int,
    data: FundingServiceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    record = db.get(FundingServiceApplication, record_id)
    if not record:
        raise HTTPException(404, "Funding service registration not found")

    values = data.model_dump(exclude_unset=True)

    if "service_code" in values:
        catalog = SERVICE_CATALOG[values["service_code"]]
        values["service_name"] = catalog["name"]
        values["service_fee"] = catalog["fee"]

    if values.get("assigned_to_id"):
        assignee = db.get(User, values["assigned_to_id"])
        if not assignee or not assignee.is_active:
            raise HTTPException(400, "Invalid administrator assignment")

    if "entrepreneur_application_id" in values and values["entrepreneur_application_id"]:
        agristart = db.get(
            EntrepreneurshipApplication,
            values["entrepreneur_application_id"],
        )
        if not agristart:
            raise HTTPException(404, "AgriStart application not found")
        values["agristart_reference"] = agristart.reference

    changes = {}
    for field, value in values.items():
        old_value = getattr(record, field, None)
        setattr(record, field, value)
        changes[field] = {"from": str(old_value), "to": str(value)}

    audit(
        db,
        user,
        "Updated funding service registration",
        "funding_service",
        record.id,
        {"reference": record.reference, "changes": changes},
        request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(record)
    return serialize(record)
