from __future__ import annotations
import hashlib, hmac, io, json, smtplib
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from decimal import Decimal
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse, Response, HTMLResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from .config import get_settings
from .database import get_db
from .deps import current_user
from .models import (User, Farmer, Buyer, Order, MembershipApplication, Payment,
    InventoryLot, Vehicle, Dispatch, QualityCase, Invoice, SupplierPayment,
    PaymentTransaction, RefundRecord, StoredDocument, Notification)
from .utils import make_reference, audit

router = APIRouter(prefix="/api")
settings = get_settings()

def serialize(rec):
    return {c.name:getattr(rec,c.name) for c in rec.__table__.columns if c.name != "file_data"}

def role_required(*roles):
    def dep(user: User = Depends(current_user)):
        if user.role not in roles and user.role != "CEO":
            raise HTTPException(403, "Insufficient role permissions")
        return user
    return dep

class InventoryIn(BaseModel):
    farmer_id:int; egg_size:str; packaging:str; trays_available:int=Field(ge=0); unit_price:float|None=None
    available_from:date=date.today(); expiry_date:date|None=None; status:str="Available"; notes:str|None=None
class VehicleIn(BaseModel):
    registration:str; vehicle_type:str; capacity_trays:int=Field(ge=0); driver_name:str|None=None; driver_phone:str|None=None; status:str="Available"; next_service_date:date|None=None
class DispatchIn(BaseModel):
    order_id:int; vehicle_id:int|None=None; driver_name:str|None=None; collection_location:str; delivery_location:str
    scheduled_date:datetime; trays:int=Field(ge=0); status:str="Scheduled"; tracking_note:str|None=None
class QualityIn(BaseModel):
    order_id:int|None=None; farmer_id:int|None=None; case_type:str; trays_affected:int=Field(ge=0); severity:str="Medium"; status:str="Open"; findings:str|None=None; corrective_action:str|None=None
class InvoiceIn(BaseModel):
    entity_type:str; entity_id:int; customer_name:str; customer_email:EmailStr|None=None; description:str
    subtotal:float=Field(ge=0); tax_amount:float=Field(ge=0,default=0); due_date:date
class SupplierPaymentIn(BaseModel):
    farmer_id:int; order_id:int|None=None; amount:float=Field(gt=0); method:str="EFT"; bank_reference:str|None=None; status:str="Pending"; scheduled_date:date|None=None
class PaymentInitIn(BaseModel):
    entity_type:str; entity_id:int; payer_email:EmailStr; amount:float=Field(gt=0); callback_url:str|None=None
class RefundIn(BaseModel):
    payment_transaction_id:int; amount:float=Field(gt=0); reason:str
class NotificationIn(BaseModel):
    channel:str; recipient:str; subject:str|None=None; message:str

@router.get('/admin/analytics')
def analytics(db:Session=Depends(get_db), user:User=Depends(current_user)):
    today=datetime.utcnow().date(); month_start=today.replace(day=1)
    paid_statuses=["Paid","Success","Successful"]
    today_revenue=float(db.scalar(select(func.coalesce(func.sum(Payment.amount),0)).where(Payment.status.in_(paid_statuses),func.date(Payment.updated_at)==today)) or 0)
    month_revenue=float(db.scalar(select(func.coalesce(func.sum(Payment.amount),0)).where(Payment.status.in_(paid_statuses),func.date(Payment.updated_at)>=month_start)) or 0)
    total_trays=0
    for q in db.scalars(select(Order.quantity)).all():
        try: total_trays += int(''.join(ch for ch in str(q) if ch.isdigit()) or 0)
        except: pass
    active_farmers=db.scalar(select(func.count()).select_from(Farmer).where(Farmer.status=="Approved")) or 0
    active_buyers=db.scalar(select(func.count()).select_from(Buyer).where(Buyer.status=="Approved")) or 0
    membership_growth=[]; revenue_series=[]; order_series=[]
    for i in range(5,-1,-1):
        start=(today.replace(day=1)-timedelta(days=32*i)).replace(day=1)
        end=(start+timedelta(days=32)).replace(day=1)
        label=start.strftime('%b')
        membership_growth.append({"label":label,"value":db.scalar(select(func.count()).select_from(MembershipApplication).where(MembershipApplication.created_at>=start,MembershipApplication.created_at<end)) or 0})
        revenue_series.append({"label":label,"value":float(db.scalar(select(func.coalesce(func.sum(Payment.amount),0)).where(Payment.status.in_(paid_statuses),Payment.created_at>=start,Payment.created_at<end)) or 0)})
        order_series.append({"label":label,"value":db.scalar(select(func.count()).select_from(Order).where(Order.created_at>=start,Order.created_at<end)) or 0})
    provinces={}
    for loc in db.scalars(select(Farmer.location)).all():
        key=(loc or 'Unspecified').split(',')[-1].strip(); provinces[key]=provinces.get(key,0)+1
    top_buyers=[{"name":n,"orders":c} for n,c in db.execute(select(Order.business_name,func.count(Order.id)).group_by(Order.business_name).order_by(desc(func.count(Order.id))).limit(5)).all()]
    top_suppliers=[{"name":n,"capacity":int(c or 0)} for n,c in db.execute(select(Farmer.farm_name,Farmer.weekly_capacity).order_by(desc(Farmer.weekly_capacity)).limit(5)).all()]
    delivered=db.scalar(select(func.count()).select_from(Dispatch).where(Dispatch.status=="Delivered")) or 0
    total_dispatch=db.scalar(select(func.count()).select_from(Dispatch)) or 0
    return {"today_revenue":today_revenue,"month_revenue":month_revenue,"total_trays":total_trays,"active_farmers":active_farmers,"active_buyers":active_buyers,
            "top_buyers":top_buyers,"top_suppliers":top_suppliers,"provinces":provinces,"membership_growth":membership_growth,"revenue_series":revenue_series,"order_series":order_series,
            "delivery_performance":round((delivered/total_dispatch*100),1) if total_dispatch else 0}

@router.get('/admin/inventory')
def list_inventory(db:Session=Depends(get_db), user:User=Depends(current_user)):
    rows=db.scalars(select(InventoryLot).order_by(desc(InventoryLot.created_at))).all(); return [{**serialize(r),"farmer_name":r.farmer.farm_name if r.farmer else None} for r in rows]
@router.post('/admin/inventory',status_code=201)
def create_inventory(data:InventoryIn,db:Session=Depends(get_db),user:User=Depends(role_required("ADMIN","OPERATIONS","QUALITY"))):
    if not db.get(Farmer,data.farmer_id): raise HTTPException(404,"Farmer not found")
    r=InventoryLot(reference=make_reference("INV"),**data.model_dump()); db.add(r); db.flush(); audit(db,user,"Created inventory lot","inventory",r.id); db.commit(); return serialize(r)
@router.patch('/admin/inventory/{id}')
def update_inventory(id:int,data:InventoryIn,db:Session=Depends(get_db),user:User=Depends(role_required("ADMIN","OPERATIONS","QUALITY"))):
    r=db.get(InventoryLot,id)
    if not r: raise HTTPException(404,"Inventory lot not found")
    for k,v in data.model_dump().items(): setattr(r,k,v)
    audit(db,user,"Updated inventory lot","inventory",r.id); db.commit(); return serialize(r)

@router.get('/admin/vehicles')
def vehicles(db:Session=Depends(get_db),user:User=Depends(current_user)):
    return [serialize(x) for x in db.scalars(select(Vehicle).order_by(Vehicle.registration)).all()]
@router.post('/admin/vehicles',status_code=201)
def create_vehicle(data:VehicleIn,db:Session=Depends(get_db),user:User=Depends(role_required("ADMIN","LOGISTICS","OPERATIONS"))):
    if db.scalar(select(Vehicle).where(Vehicle.registration==data.registration.upper())): raise HTTPException(409,"Vehicle already exists")
    r=Vehicle(**data.model_dump()); r.registration=r.registration.upper(); db.add(r); db.flush(); audit(db,user,"Added vehicle","vehicle",r.id); db.commit(); return serialize(r)

@router.get('/admin/dispatches')
def dispatches(db:Session=Depends(get_db),user:User=Depends(current_user)):
    rows=db.scalars(select(Dispatch).order_by(desc(Dispatch.scheduled_date))).all()
    return [{**serialize(r),"order_reference":r.order.reference if r.order else None,"vehicle_registration":r.vehicle.registration if r.vehicle else None} for r in rows]
@router.post('/admin/dispatches',status_code=201)
def create_dispatch(data:DispatchIn,db:Session=Depends(get_db),user:User=Depends(role_required("ADMIN","LOGISTICS","OPERATIONS"))):
    if not db.get(Order,data.order_id): raise HTTPException(404,"Order not found")
    r=Dispatch(reference=make_reference("DSP"),**data.model_dump()); db.add(r); db.flush(); audit(db,user,"Scheduled dispatch","dispatch",r.id); db.commit(); return serialize(r)
@router.patch('/admin/dispatches/{id}')
def update_dispatch(id:int,data:DispatchIn,db:Session=Depends(get_db),user:User=Depends(role_required("ADMIN","LOGISTICS","OPERATIONS"))):
    r=db.get(Dispatch,id)
    if not r: raise HTTPException(404,"Dispatch not found")
    for k,v in data.model_dump().items(): setattr(r,k,v)
    if r.status=="Dispatched" and not r.dispatched_at:r.dispatched_at=datetime.utcnow()
    if r.status=="Delivered" and not r.delivered_at:r.delivered_at=datetime.utcnow()
    audit(db,user,"Updated dispatch","dispatch",r.id); db.commit(); return serialize(r)

@router.get('/admin/quality-cases')
def quality_cases(db:Session=Depends(get_db),user:User=Depends(current_user)):
    return [serialize(x) for x in db.scalars(select(QualityCase).order_by(desc(QualityCase.created_at))).all()]
@router.post('/admin/quality-cases',status_code=201)
def create_quality(data:QualityIn,db:Session=Depends(get_db),user:User=Depends(role_required("ADMIN","QUALITY","OPERATIONS"))):
    r=QualityCase(reference=make_reference("QC"),**data.model_dump()); db.add(r); db.flush(); audit(db,user,"Opened quality case","quality_case",r.id); db.commit(); return serialize(r)
@router.patch('/admin/quality-cases/{id}')
def update_quality(id:int,data:QualityIn,db:Session=Depends(get_db),user:User=Depends(role_required("ADMIN","QUALITY","OPERATIONS"))):
    r=db.get(QualityCase,id)
    if not r: raise HTTPException(404,"Quality case not found")
    for k,v in data.model_dump().items(): setattr(r,k,v)
    if r.status=="Resolved" and not r.resolved_at:r.resolved_at=datetime.utcnow()
    audit(db,user,"Updated quality case","quality_case",r.id); db.commit(); return serialize(r)

@router.get('/admin/invoices')
def invoices(db:Session=Depends(get_db),user:User=Depends(current_user)):
    return [serialize(x) for x in db.scalars(select(Invoice).order_by(desc(Invoice.created_at))).all()]
@router.post('/admin/invoices',status_code=201)
def create_invoice(data:InvoiceIn,db:Session=Depends(get_db),user:User=Depends(role_required("ADMIN","FINANCE"))):
    total=Decimal(str(data.subtotal))+Decimal(str(data.tax_amount))
    r=Invoice(reference=make_reference("INVCE"),total_amount=total,**data.model_dump()); db.add(r); db.flush(); audit(db,user,"Created invoice","invoice",r.id); db.commit(); return serialize(r)

def invoice_pdf_bytes(inv:Invoice)->bytes:
    buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=18*mm,bottomMargin=18*mm)
    styles=getSampleStyleSheet(); story=[Paragraph("<b>FARMLINK DISTRIBUTION</b>",styles['Title']),Paragraph("A Division of Makwande Chemicals (Pty) Ltd",styles['Normal']),Spacer(1,8*mm)]
    data=[["Invoice",inv.reference],["Customer",inv.customer_name],["Issue date",inv.created_at.strftime('%d %B %Y')],["Due date",inv.due_date.strftime('%d %B %Y')],["Status",inv.status]]
    t=Table(data,colWidths=[45*mm,110*mm]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(0,-1),colors.HexColor('#073827')),('TEXTCOLOR',(0,0),(0,-1),colors.white),('GRID',(0,0),(-1,-1),.5,colors.HexColor('#d9dfdc')),('PADDING',(0,0),(-1,-1),8)])); story += [t,Spacer(1,8*mm),Paragraph(inv.description,styles['BodyText']),Spacer(1,8*mm)]
    amounts=[["Subtotal",f"R {float(inv.subtotal):,.2f}"],["Tax",f"R {float(inv.tax_amount):,.2f}"],["Total",f"R {float(inv.total_amount):,.2f}"],["Paid",f"R {float(inv.amount_paid):,.2f}"],["Balance",f"R {float(inv.total_amount-inv.amount_paid):,.2f}"]]
    at=Table(amounts,colWidths=[100*mm,55*mm]); at.setStyle(TableStyle([('ALIGN',(1,0),(1,-1),'RIGHT'),('LINEABOVE',(0,2),(-1,2),1,colors.HexColor('#b58a2c')),('FONTNAME',(0,2),(-1,2),'Helvetica-Bold'),('PADDING',(0,0),(-1,-1),7)])); story.append(at); doc.build(story); return buf.getvalue()
@router.get('/admin/invoices/{id}/pdf')
def invoice_pdf(id:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    inv=db.get(Invoice,id)
    if not inv: raise HTTPException(404,"Invoice not found")
    return Response(invoice_pdf_bytes(inv),media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename={inv.reference}.pdf'})

@router.get('/admin/supplier-payments')
def supplier_payments(db:Session=Depends(get_db),user:User=Depends(current_user)):
    rows=db.scalars(select(SupplierPayment).order_by(desc(SupplierPayment.created_at))).all(); return [{**serialize(r),"farmer_name":r.farmer.farm_name if r.farmer else None} for r in rows]
@router.post('/admin/supplier-payments',status_code=201)
def create_supplier_payment(data:SupplierPaymentIn,db:Session=Depends(get_db),user:User=Depends(role_required("ADMIN","FINANCE"))):
    if not db.get(Farmer,data.farmer_id): raise HTTPException(404,"Farmer not found")
    r=SupplierPayment(reference=make_reference("SPAY"),**data.model_dump()); db.add(r); db.flush(); audit(db,user,"Created supplier payment","supplier_payment",r.id); db.commit(); return serialize(r)


PAYSTACK_API_BASE = "https://api.paystack.co"

def _paystack_headers() -> dict[str, str]:
    if not settings.paystack_secret_key:
        raise HTTPException(503, "Paystack is not configured")
    return {
        "Authorization": f"Bearer {settings.paystack_secret_key}",
        "Content-Type": "application/json",
    }

def _payment_entity(db: Session, entity_type: str, entity_id: int):
    entity_type = entity_type.strip().lower()
    model_map = {
        "order": Order,
        "membership": MembershipApplication,
        "invoice": Invoice,
    }
    model = model_map.get(entity_type)
    if not model:
        raise HTTPException(400, "Unsupported payment entity type")
    entity = db.get(model, entity_id)
    if not entity:
        raise HTTPException(404, f"{entity_type.title()} record not found")
    return entity_type, entity

def _entity_identity(entity_type: str, entity) -> tuple[str, str | None]:
    if entity_type == "order":
        return entity.business_name, entity.email
    if entity_type == "membership":
        return entity.business_name, entity.email
    if entity_type == "invoice":
        return entity.customer_name, entity.customer_email
    return "FarmLink customer", None

def _append_internal_note(record, note: str) -> None:
    if not hasattr(record, "internal_notes"):
        return
    existing = (record.internal_notes or "").strip()
    if note in existing:
        return
    record.internal_notes = f"{existing}\n{note}".strip()

def _queue_receipt_notification(
    db: Session,
    payer_email: str,
    payer_name: str,
    reference: str,
    amount: float,
) -> None:
    existing = db.scalar(
        select(Notification).where(
            Notification.recipient == payer_email,
            Notification.subject == f"FarmLink payment receipt {reference}",
        )
    )
    if existing:
        return
    db.add(
        Notification(
            channel="Email",
            recipient=payer_email,
            subject=f"FarmLink payment receipt {reference}",
            message=(
                f"Dear {payer_name},\n\n"
                f"FarmLink Distribution has verified your payment of "
                f"R {amount:,.2f}.\n"
                f"Payment reference: {reference}\n\n"
                f"Keep this reference for your records.\n\n"
                f"FarmLink Distribution"
            ),
            status="Queued",
        )
    )

def _receipt_pdf_bytes(tx: PaymentTransaction, payer_name: str) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph("<b>FARMLINK DISTRIBUTION</b>", styles["Title"]),
        Paragraph("Payment Receipt", styles["Heading2"]),
        Paragraph("A Division of Makwande Chemicals (Pty) Ltd", styles["Normal"]),
        Spacer(1, 8 * mm),
    ]
    rows = [
        ["Receipt reference", tx.reference],
        ["Customer", payer_name],
        ["Email", tx.payer_email],
        ["Amount", f"R {float(tx.amount):,.2f}"],
        ["Currency", tx.currency],
        ["Payment provider", tx.provider],
        ["Status", tx.status],
        ["Verified date", tx.verified_at.strftime("%d %B %Y %H:%M") if tx.verified_at else "Not verified"],
    ]
    table = Table(rows, colWidths=[48 * mm, 107 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#073827")),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9dfdc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend(
        [
            table,
            Spacer(1, 8 * mm),
            Paragraph(
                "This receipt confirms a server-verified payment recorded by "
                "FarmLink Distribution. Test-mode payments do not represent real funds.",
                styles["BodyText"],
            ),
        ]
    )
    doc.build(story)
    return buf.getvalue()

def _reconcile_successful_transaction(
    db: Session,
    tx: PaymentTransaction,
    provider_data: dict,
    *,
    source: str,
    ip_address: str | None = None,
) -> dict:
    expected_amount = int(round(float(tx.amount) * 100))
    received_amount = int(provider_data.get("amount") or 0)
    currency = str(provider_data.get("currency") or "").upper()
    provider_status = str(provider_data.get("status") or "").lower()
    provider_reference = str(provider_data.get("reference") or "")

    if provider_reference != tx.reference:
        raise HTTPException(400, "Paystack reference mismatch")
    if received_amount != expected_amount:
        tx.status = "Amount mismatch"
        tx.provider_payload = provider_data
        db.commit()
        raise HTTPException(400, "Verified amount does not match the expected amount")
    if currency != "ZAR":
        tx.status = "Currency mismatch"
        tx.provider_payload = provider_data
        db.commit()
        raise HTTPException(400, "Verified currency does not match ZAR")
    if provider_status != "success":
        tx.status = provider_status.title() or "Failed"
        tx.provider_payload = provider_data
        db.commit()
        return {"verified": False, "status": tx.status, "reference": tx.reference}

    was_paid = tx.status == "Paid"
    tx.status = "Paid"
    tx.provider_payload = provider_data
    tx.verified_at = tx.verified_at or datetime.utcnow()

    entity_type, entity = _payment_entity(db, tx.entity_type, tx.entity_id)
    payer_name, entity_email = _entity_identity(entity_type, entity)
    payer_email = tx.payer_email or entity_email or ""

    channel = (
        (provider_data.get("authorization") or {}).get("channel")
        or provider_data.get("channel")
        or "Paystack"
    )
    legacy_payment = db.scalar(
        select(Payment).where(Payment.external_reference == tx.reference)
    )
    if not legacy_payment:
        legacy_payment = Payment(
            reference=make_reference("PAY"),
            entity_type=entity_type,
            entity_id=tx.entity_id,
            payer_name=payer_name,
            amount=tx.amount,
            method=f"Paystack {str(channel).title()}",
            status="Paid",
            external_reference=tx.reference,
            notes=f"Automatically reconciled from Paystack via {source}.",
        )
        db.add(legacy_payment)
        db.flush()
    else:
        legacy_payment.status = "Paid"
        legacy_payment.amount = tx.amount
        legacy_payment.method = f"Paystack {str(channel).title()}"
        legacy_payment.notes = f"Automatically reconciled from Paystack via {source}."

    if entity_type == "invoice":
        entity.amount_paid = max(float(entity.amount_paid or 0), float(tx.amount))
        balance = float(entity.total_amount) - float(entity.amount_paid)
        entity.status = "Paid" if balance <= 0.009 else "Part paid"
    elif entity_type == "membership":
        if entity.status == "Pending":
            entity.status = "Approved"
        _append_internal_note(entity, f"Paystack payment verified: {tx.reference}")
    elif entity_type == "order":
        if entity.status == "Pending":
            entity.status = "Approved"
        _append_internal_note(entity, f"Paystack payment verified: {tx.reference}")

    if not was_paid:
        _queue_receipt_notification(
            db,
            payer_email=tx.payer_email,
            payer_name=payer_name,
            reference=tx.reference,
            amount=float(tx.amount),
        )
        audit(
            db,
            None,
            "Verified Paystack payment",
            "payment_transaction",
            tx.id,
            {
                "reference": tx.reference,
                "entity_type": entity_type,
                "entity_id": tx.entity_id,
                "amount": float(tx.amount),
                "source": source,
            },
            ip_address,
        )

    db.commit()
    return {
        "verified": True,
        "status": tx.status,
        "reference": tx.reference,
        "payment_id": legacy_payment.id,
        "receipt_url": f"/api/payments/receipt/{tx.reference}",
    }

@router.post("/payments/paystack/initialize")
def paystack_initialize(data: PaymentInitIn, db: Session = Depends(get_db)):
    entity_type, entity = _payment_entity(db, data.entity_type, data.entity_id)
    payer_name, entity_email = _entity_identity(entity_type, entity)
    payer_email = str(data.payer_email).strip().lower()

    if entity_email and payer_email != str(entity_email).strip().lower():
        # Do not block legitimate alternate payer emails, but preserve both in metadata.
        customer_email = str(entity_email).strip().lower()
    else:
        customer_email = payer_email

    reference = make_reference("PSTK")
    callback_url = (
        data.callback_url
        or settings.paystack_callback_url
        or f"{settings.public_base_url.rstrip('/')}/api/payments/paystack/callback"
    )
    payload = {
        "email": payer_email,
        "amount": str(int(round(data.amount * 100))),
        "currency": "ZAR",
        "reference": reference,
        "callback_url": callback_url,
        "metadata": json.dumps(
            {
                "entity_type": entity_type,
                "entity_id": data.entity_id,
                "payer_name": payer_name,
                "customer_email": customer_email,
            }
        ),
    }

    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{PAYSTACK_API_BASE}/transaction/initialize",
                json=payload,
                headers=_paystack_headers(),
            )
        result = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, f"Unable to initialize Paystack payment: {exc}") from exc

    if not response.is_success or not result.get("status"):
        raise HTTPException(
            502,
            result.get("message", "Paystack transaction initialization failed"),
        )

    tx = PaymentTransaction(
        reference=reference,
        entity_type=entity_type,
        entity_id=data.entity_id,
        payer_email=payer_email,
        amount=data.amount,
        currency="ZAR",
        status="Initialized",
        authorization_url=result["data"]["authorization_url"],
        provider_payload=result,
    )
    db.add(tx)
    db.flush()
    audit(
        db,
        None,
        "Initialized Paystack payment",
        "payment_transaction",
        tx.id,
        {
            "reference": reference,
            "entity_type": entity_type,
            "entity_id": data.entity_id,
            "amount": data.amount,
        },
    )
    db.commit()
    return {
        "reference": reference,
        "authorization_url": tx.authorization_url,
        "access_code": result["data"].get("access_code"),
        "status": tx.status,
    }

def verify_paystack(reference: str, db: Session, *, source: str = "verification endpoint"):
    tx = db.scalar(
        select(PaymentTransaction).where(PaymentTransaction.reference == reference)
    )
    if not tx:
        raise HTTPException(404, "FarmLink payment transaction not found")

    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(
                f"{PAYSTACK_API_BASE}/transaction/verify/{reference}",
                headers=_paystack_headers(),
            )
        result = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, f"Unable to verify Paystack payment: {exc}") from exc

    if not response.is_success or not result.get("status"):
        raise HTTPException(
            502,
            result.get("message", "Paystack verification failed"),
        )

    return _reconcile_successful_transaction(
        db,
        tx,
        result.get("data") or {},
        source=source,
    )

@router.get("/payments/paystack/verify/{reference}")
def verify_payment(reference: str, db: Session = Depends(get_db)):
    return verify_paystack(reference, db)

@router.get("/payments/paystack/callback", response_class=HTMLResponse)
def paystack_callback(reference: str, db: Session = Depends(get_db)):
    try:
        result = verify_paystack(reference, db, source="callback")
        success = bool(result.get("verified"))
        heading = "Payment verified" if success else "Payment not completed"
        message = (
            f"Reference {reference} has been verified successfully."
            if success
            else f"Reference {reference} has not been completed."
        )
        receipt = (
            f'<a class="button" href="/api/payments/receipt/{reference}">Download receipt</a>'
            if success
            else ""
        )
    except HTTPException as exc:
        heading = "Payment verification failed"
        message = str(exc.detail)
        receipt = ""

    return HTMLResponse(
        f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{heading} | FarmLink Distribution</title>
<style>
body{{margin:0;font-family:Inter,Arial,sans-serif;background:#f3f6f4;color:#102119;display:grid;place-items:center;min-height:100vh;padding:20px}}
.card{{max-width:560px;background:white;border:1px solid #dfe6e2;border-radius:22px;padding:38px;box-shadow:0 24px 70px rgba(7,56,39,.12)}}
.kicker{{color:#b58a2c;text-transform:uppercase;letter-spacing:.13em;font-weight:800;font-size:12px}}
h1{{font-size:34px;margin:10px 0}}p{{color:#617068;line-height:1.6}}
.ref{{font-family:monospace;background:#eef4f1;padding:10px;border-radius:9px}}
.button{{display:inline-block;margin-top:15px;background:#073827;color:white;text-decoration:none;padding:13px 18px;border-radius:10px;font-weight:800}}
</style></head>
<body><main class="card"><span class="kicker">FarmLink Distribution</span><h1>{heading}</h1>
<p>{message}</p><p class="ref">{reference}</p>{receipt}</main></body></html>"""
    )

@router.post("/payments/paystack/webhook")
async def paystack_webhook(request: Request, db: Session = Depends(get_db)):
    raw = await request.body()
    signature = request.headers.get("x-paystack-signature", "")
    if not settings.paystack_secret_key:
        raise HTTPException(503, "Paystack is not configured")

    expected = hmac.new(
        settings.paystack_secret_key.encode("utf-8"),
        raw,
        hashlib.sha512,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(401, "Invalid Paystack webhook signature")

    try:
        event = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "Invalid webhook payload") from exc

    if event.get("event") != "charge.success":
        return {"received": True, "processed": False}

    provider_data = event.get("data") or {}
    reference = provider_data.get("reference")
    if not reference:
        return {"received": True, "processed": False}

    tx = db.scalar(
        select(PaymentTransaction).where(PaymentTransaction.reference == reference)
    )
    if not tx:
        # A transaction not initialized by FarmLink must not create internal value.
        audit(
            db,
            None,
            "Ignored unknown Paystack webhook",
            "payment_transaction",
            None,
            {"reference": reference},
            request.client.host if request.client else None,
        )
        db.commit()
        return {"received": True, "processed": False, "reason": "Unknown reference"}

    result = _reconcile_successful_transaction(
        db,
        tx,
        provider_data,
        source="signed webhook",
        ip_address=request.client.host if request.client else None,
    )
    return {"received": True, "processed": True, **result}

@router.get("/payments/receipt/{reference}")
def payment_receipt(reference: str, db: Session = Depends(get_db)):
    tx = db.scalar(
        select(PaymentTransaction).where(PaymentTransaction.reference == reference)
    )
    if not tx:
        raise HTTPException(404, "Payment transaction not found")
    if tx.status != "Paid":
        raise HTTPException(409, "Receipt is available only for verified payments")
    entity_type, entity = _payment_entity(db, tx.entity_type, tx.entity_id)
    payer_name, _ = _entity_identity(entity_type, entity)
    return Response(
        _receipt_pdf_bytes(tx, payer_name),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="FarmLink-{reference}-receipt.pdf"'
        },
    )

@router.get("/admin/payment-transactions")
def payment_transactions(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    rows = db.scalars(
        select(PaymentTransaction).order_by(desc(PaymentTransaction.created_at))
    ).all()
    return [
        {
            **serialize(tx),
            "receipt_url": (
                f"/api/payments/receipt/{tx.reference}" if tx.status == "Paid" else None
            ),
        }
        for tx in rows
    ]

@router.post("/admin/payment-transactions/{reference}/reconcile")
def reconcile_payment_transaction(
    reference: str,
    db: Session = Depends(get_db),
    user: User = Depends(role_required("ADMIN", "FINANCE")),
):
    result = verify_paystack(reference, db, source=f"manual reconciliation by {user.full_name}")
    tx = db.scalar(
        select(PaymentTransaction).where(PaymentTransaction.reference == reference)
    )
    audit(
        db,
        user,
        "Manually reconciled Paystack payment",
        "payment_transaction",
        tx.id if tx else None,
        {"reference": reference, "result": result},
    )
    db.commit()
    return result

@router.post('/admin/refunds',status_code=201)
def create_refund(data:RefundIn,db:Session=Depends(get_db),user:User=Depends(role_required("ADMIN","FINANCE"))):
    tx=db.get(PaymentTransaction,data.payment_transaction_id)
    if not tx: raise HTTPException(404,"Transaction not found")
    r=RefundRecord(reference=make_reference("REF"),**data.model_dump()); db.add(r); db.flush(); audit(db,user,"Requested refund","refund",r.id); db.commit(); return serialize(r)
@router.get('/admin/refunds')
def refunds(db:Session=Depends(get_db),user:User=Depends(current_user)):
    return [serialize(x) for x in db.scalars(select(RefundRecord).order_by(desc(RefundRecord.created_at))).all()]

@router.post('/admin/documents',status_code=201)
async def upload_document(entity_type:str=Form(...),entity_id:int=Form(...),document_type:str=Form(...),file:UploadFile=File(...),db:Session=Depends(get_db),user:User=Depends(current_user)):
    data=await file.read()
    if len(data)>10*1024*1024: raise HTTPException(413,"File exceeds 10 MB")
    r=StoredDocument(reference=make_reference("DOC"),entity_type=entity_type,entity_id=entity_id,document_type=document_type,filename=file.filename or 'document',content_type=file.content_type or 'application/octet-stream',file_size=len(data),file_data=data,uploaded_by_id=user.id)
    db.add(r); db.flush(); audit(db,user,"Uploaded document","document",r.id); db.commit(); return serialize(r)
@router.get('/admin/documents')
def documents(entity_type:str|None=None,entity_id:int|None=None,db:Session=Depends(get_db),user:User=Depends(current_user)):
    stmt=select(StoredDocument)
    if entity_type: stmt=stmt.where(StoredDocument.entity_type==entity_type)
    if entity_id: stmt=stmt.where(StoredDocument.entity_id==entity_id)
    return [serialize(x) for x in db.scalars(stmt.order_by(desc(StoredDocument.created_at))).all()]
@router.get('/admin/documents/{id}/download')
def download_document(id:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    r=db.get(StoredDocument,id)
    if not r: raise HTTPException(404,"Document not found")
    return Response(r.file_data,media_type=r.content_type,headers={'Content-Disposition':f'attachment; filename="{r.filename}"'})

@router.get('/admin/notifications')
def notifications(db:Session=Depends(get_db),user:User=Depends(current_user)):
    return [serialize(x) for x in db.scalars(select(Notification).order_by(desc(Notification.created_at)).limit(300)).all()]

def send_email_notification(n:Notification):
    if not all([settings.smtp_host,settings.smtp_username,settings.smtp_password,settings.smtp_from_email]):
        n.status='Queued'; n.error='SMTP credentials not configured'; return
    msg=EmailMessage(); msg['From']=settings.smtp_from_email; msg['To']=n.recipient; msg['Subject']=n.subject or 'FarmLink notification'; msg.set_content(n.message)
    with smtplib.SMTP(settings.smtp_host,settings.smtp_port,timeout=20) as smtp:
        smtp.starttls(); smtp.login(settings.smtp_username,settings.smtp_password); smtp.send_message(msg)
    n.status='Sent'; n.sent_at=datetime.utcnow(); n.error=None
@router.post('/admin/notifications',status_code=201)
def create_notification(data:NotificationIn,db:Session=Depends(get_db),user:User=Depends(current_user)):
    n=Notification(**data.model_dump()); db.add(n); db.flush()
    try:
        if n.channel.lower()=='email': send_email_notification(n)
        else: n.status='Queued'; n.error='External provider credentials required for this channel'
    except Exception as exc: n.status='Failed'; n.error=str(exc)[:1000]
    audit(db,user,"Created notification","notification",n.id); db.commit(); return serialize(n)
