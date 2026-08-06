from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from .database import get_db
from .deps import current_user
from .models import (
    Buyer,
    Dispatch,
    Farmer,
    Invoice,
    InventoryLot,
    Notification,
    Order,
    SupplierPayment,
    User,
)
from .phase4_models import BuyerRequirement, SupplierBuyerMatch
from .phase5_models import CommercialDeal, DealTimelineEvent
from .phase5_schemas import DealCreate, DealEventCreate, DealUpdate
from .utils import audit, make_reference


router = APIRouter(prefix="/api", tags=["Commercial Fulfilment Phase 5"])


def serialize(record) -> dict:
    result = {
        column.name: getattr(record, column.name)
        for column in record.__table__.columns
    }
    for key in (
        "unit_price",
        "supplier_unit_cost",
        "delivery_cost",
        "transaction_cost",
        "service_fee",
        "subtotal",
        "total_amount",
        "supplier_amount",
        "gross_margin",
    ):
        if key in result and result[key] is not None:
            result[key] = float(result[key])
    return result


def quantity_number(value: str) -> int:
    digits = re.findall(r"\d+", value or "")
    return int(digits[0]) if digits else 1


def add_event(
    db: Session,
    deal: CommercialDeal,
    title: str,
    detail: str | None,
    actor_id: int | None,
    event_type: str = "Status",
) -> DealTimelineEvent:
    event = DealTimelineEvent(
        deal_id=deal.id,
        event_type=event_type,
        title=title,
        detail=detail,
        actor_id=actor_id,
    )
    db.add(event)
    return event


def notify(
    db: Session,
    recipient: str | None,
    subject: str,
    message: str,
) -> None:
    if not recipient:
        return
    db.add(
        Notification(
            channel="Email",
            recipient=recipient,
            subject=subject,
            message=message,
            status="Queued",
        )
    )


def deal_detail(db: Session, deal: CommercialDeal) -> dict:
    result = serialize(deal)
    result["farmer"] = serialize(db.get(Farmer, deal.farmer_id))
    result["buyer"] = serialize(db.get(Buyer, deal.buyer_id))
    result["order"] = (
        serialize(db.get(Order, deal.order_id)) if deal.order_id else None
    )
    result["invoice"] = (
        serialize(db.get(Invoice, deal.invoice_id)) if deal.invoice_id else None
    )
    result["dispatch"] = (
        serialize(db.get(Dispatch, deal.dispatch_id)) if deal.dispatch_id else None
    )
    result["supplier_payment"] = (
        serialize(db.get(SupplierPayment, deal.supplier_payment_id))
        if deal.supplier_payment_id
        else None
    )
    result["timeline"] = [
        serialize(item)
        for item in db.scalars(
            select(DealTimelineEvent)
            .where(DealTimelineEvent.deal_id == deal.id)
            .order_by(DealTimelineEvent.created_at)
        ).all()
    ]
    return result


@router.get("/admin/phase5/dashboard")
def phase5_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    rows = db.scalars(
        select(CommercialDeal).order_by(desc(CommercialDeal.created_at))
    ).all()
    paid = [row for row in rows if row.payment_status == "Paid"]
    completed = [row for row in rows if row.status == "Completed"]
    return {
        "summary": {
            "total_deals": len(rows),
            "awaiting_acceptance": sum(
                1
                for row in rows
                if row.buyer_acceptance_status != "Accepted"
                or row.supplier_acceptance_status != "Accepted"
            ),
            "awaiting_payment": sum(
                1 for row in rows if row.payment_status != "Paid"
            ),
            "in_fulfilment": sum(
                1
                for row in rows
                if row.fulfilment_status
                in {"Inventory reserved", "Scheduled", "Dispatched"}
            ),
            "completed": len(completed),
            "revenue": float(sum(row.total_amount for row in paid)),
            "gross_margin": float(sum(row.gross_margin for row in completed)),
        },
        "items": [deal_detail(db, row) for row in rows],
    }


@router.post("/admin/phase5/deals", status_code=201)
def create_deal(
    data: DealCreate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    match = db.get(SupplierBuyerMatch, data.supplier_match_id)
    if not match:
        raise HTTPException(404, "Supplier-buyer match not found")
    if match.status not in {
        "Shortlisted",
        "Introduced",
        "Negotiating",
        "Successful",
    }:
        raise HTTPException(
            409,
            "The supplier match must be shortlisted or introduced first",
        )
    existing = db.scalar(
        select(CommercialDeal).where(
            CommercialDeal.supplier_match_id == data.supplier_match_id
        )
    )
    if existing:
        raise HTTPException(409, "A commercial deal already exists for this match")

    requirement = db.get(BuyerRequirement, match.buyer_requirement_id)
    if not requirement:
        raise HTTPException(404, "Buyer requirement not found")
    buyer = db.get(Buyer, requirement.buyer_id)
    farmer = db.get(Farmer, match.farmer_id) if match.farmer_id else None
    if not buyer or not farmer:
        raise HTTPException(409, "Buyer and activated farmer records are required")

    qty = quantity_number(data.quantity)
    subtotal = Decimal(data.unit_price) * qty
    supplier_amount = Decimal(data.supplier_unit_cost) * qty
    total = (
        subtotal
        + Decimal(data.delivery_cost)
        + Decimal(data.transaction_cost)
        + Decimal(data.service_fee)
    )
    gross_margin = (
        total
        - supplier_amount
        - Decimal(data.delivery_cost)
        - Decimal(data.transaction_cost)
    )

    deal = CommercialDeal(
        reference=make_reference("DEAL"),
        supplier_match_id=match.id,
        farmer_id=farmer.id,
        buyer_id=buyer.id,
        product_description=data.product_description,
        quantity=data.quantity,
        unit_price=data.unit_price,
        supplier_unit_cost=data.supplier_unit_cost,
        delivery_cost=data.delivery_cost,
        transaction_cost=data.transaction_cost,
        service_fee=data.service_fee,
        subtotal=subtotal,
        total_amount=total,
        supplier_amount=supplier_amount,
        gross_margin=gross_margin,
        terms=data.terms,
        created_by_id=user.id,
    )
    db.add(deal)
    db.flush()
    add_event(
        db,
        deal,
        "Commercial quotation created",
        f"Deal created from match {match.reference}.",
        user.id,
        "Quotation",
    )
    match.status = "Negotiating"
    audit(
        db,
        user,
        "Created commercial deal",
        "commercial_deal",
        deal.id,
        {"reference": deal.reference, "match_reference": match.reference},
        request.client.host if request.client else None,
    )
    db.commit()
    return deal_detail(db, deal)


@router.get("/admin/phase5/deals/{deal_id}")
def get_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    deal = db.get(CommercialDeal, deal_id)
    if not deal:
        raise HTTPException(404, "Commercial deal not found")
    return deal_detail(db, deal)


@router.patch("/admin/phase5/deals/{deal_id}")
def update_deal(
    deal_id: int,
    data: DealUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    deal = db.get(CommercialDeal, deal_id)
    if not deal:
        raise HTTPException(404, "Commercial deal not found")
    values = data.model_dump(exclude_unset=True)
    for field, value in values.items():
        setattr(deal, field, value)
    if (
        deal.buyer_acceptance_status == "Accepted"
        and deal.supplier_acceptance_status == "Accepted"
        and not deal.accepted_at
    ):
        deal.accepted_at = datetime.utcnow()
        deal.status = "Accepted"
        add_event(
            db,
            deal,
            "Commercial terms accepted",
            "Buyer and supplier accepted the transaction terms.",
            user.id,
            "Acceptance",
        )
    if values.get("status") == "Completed" and not deal.completed_at:
        deal.completed_at = datetime.utcnow()
    audit(db, user, "Updated commercial deal", "commercial_deal", deal.id, values)
    db.commit()
    return deal_detail(db, deal)


@router.post("/admin/phase5/deals/{deal_id}/events", status_code=201)
def create_deal_event(
    deal_id: int,
    data: DealEventCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    deal = db.get(CommercialDeal, deal_id)
    if not deal:
        raise HTTPException(404, "Commercial deal not found")
    event = add_event(
        db,
        deal,
        data.title,
        data.detail,
        user.id,
        data.event_type,
    )
    db.commit()
    return serialize(event)


@router.post("/admin/phase5/deals/{deal_id}/create-order", status_code=201)
def create_order_from_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    deal = db.get(CommercialDeal, deal_id)
    if not deal:
        raise HTTPException(404, "Commercial deal not found")
    if deal.order_id:
        raise HTTPException(409, "Order already created")
    if not deal.accepted_at:
        raise HTTPException(409, "Buyer and supplier must accept the deal first")

    farmer = db.get(Farmer, deal.farmer_id)
    buyer = db.get(Buyer, deal.buyer_id)
    order = Order(
        reference=make_reference("ORD"),
        business_name=buyer.business_name,
        contact_person=buyer.contact_person,
        phone=buyer.phone,
        email=buyer.email,
        customer_type=buyer.category,
        delivery_area=buyer.location,
        egg_size=deal.product_description[:100],
        packaging=farmer.packaging or "To be confirmed",
        quantity=deal.quantity,
        frequency="Commercial deal",
        required_date=date.today() + timedelta(days=7),
        notes=f"Created from commercial deal {deal.reference}",
        status="Approved",
        assigned_to_id=user.id,
        quoted_amount=deal.total_amount,
    )
    db.add(order)
    db.flush()
    deal.order_id = order.id
    deal.status = "Order created"
    add_event(
        db,
        deal,
        "Sales order created",
        f"Order reference {order.reference}.",
        user.id,
        "Order",
    )
    notify(
        db,
        buyer.email,
        f"FarmLink order {order.reference}",
        f"Your order has been created from commercial deal {deal.reference}.",
    )
    db.commit()
    return serialize(order)


@router.post("/admin/phase5/deals/{deal_id}/create-invoice", status_code=201)
def create_invoice_from_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    deal = db.get(CommercialDeal, deal_id)
    if not deal:
        raise HTTPException(404, "Commercial deal not found")
    if deal.invoice_id:
        raise HTTPException(409, "Invoice already created")
    if not deal.order_id:
        raise HTTPException(409, "Create the sales order first")
    buyer = db.get(Buyer, deal.buyer_id)
    invoice = Invoice(
        reference=make_reference("INVCE"),
        entity_type="order",
        entity_id=deal.order_id,
        customer_name=buyer.business_name,
        customer_email=buyer.email,
        description=(
            f"{deal.product_description}; quantity {deal.quantity}; "
            f"commercial deal {deal.reference}"
        ),
        subtotal=deal.total_amount,
        tax_amount=0,
        total_amount=deal.total_amount,
        amount_paid=0,
        status="Unpaid",
        due_date=date.today() + timedelta(days=7),
    )
    db.add(invoice)
    db.flush()
    deal.invoice_id = invoice.id
    deal.status = "Invoiced"
    deal.payment_status = "Invoiced"
    add_event(
        db,
        deal,
        "Invoice issued",
        f"Invoice reference {invoice.reference}.",
        user.id,
        "Invoice",
    )
    notify(
        db,
        buyer.email,
        f"FarmLink invoice {invoice.reference}",
        f"Invoice {invoice.reference} has been issued for R {float(invoice.total_amount):,.2f}.",
    )
    db.commit()
    return serialize(invoice)


@router.post("/admin/phase5/deals/{deal_id}/reserve-inventory")
def reserve_inventory(
    deal_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    deal = db.get(CommercialDeal, deal_id)
    if not deal:
        raise HTTPException(404, "Commercial deal not found")
    required = quantity_number(deal.quantity)
    lots = db.scalars(
        select(InventoryLot)
        .where(
            InventoryLot.farmer_id == deal.farmer_id,
            InventoryLot.status == "Available",
            InventoryLot.trays_available > 0,
        )
        .order_by(InventoryLot.available_from)
    ).all()
    remaining = required
    allocations = []
    for lot in lots:
        if remaining <= 0:
            break
        take = min(remaining, lot.trays_available)
        lot.trays_available -= take
        remaining -= take
        if lot.trays_available == 0:
            lot.status = "Reserved"
        allocations.append({"inventory_reference": lot.reference, "quantity": take})
    if remaining > 0:
        raise HTTPException(
            409,
            f"Insufficient inventory. {remaining} units remain unallocated.",
        )
    deal.fulfilment_status = "Inventory reserved"
    add_event(
        db,
        deal,
        "Inventory reserved",
        str(allocations),
        user.id,
        "Inventory",
    )
    db.commit()
    return {"allocated": allocations}


@router.post("/admin/phase5/deals/{deal_id}/schedule-dispatch", status_code=201)
def schedule_dispatch(
    deal_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    deal = db.get(CommercialDeal, deal_id)
    if not deal:
        raise HTTPException(404, "Commercial deal not found")
    if deal.dispatch_id:
        raise HTTPException(409, "Dispatch already scheduled")
    if not deal.order_id:
        raise HTTPException(409, "Order is required before dispatch")
    farmer = db.get(Farmer, deal.farmer_id)
    buyer = db.get(Buyer, deal.buyer_id)
    dispatch = Dispatch(
        reference=make_reference("DSP"),
        order_id=deal.order_id,
        vehicle_id=None,
        driver_name=None,
        collection_location=farmer.location,
        delivery_location=buyer.location,
        scheduled_date=datetime.utcnow() + timedelta(days=3),
        trays=quantity_number(deal.quantity),
        status="Scheduled",
        tracking_note=f"Commercial deal {deal.reference}",
    )
    db.add(dispatch)
    db.flush()
    deal.dispatch_id = dispatch.id
    deal.fulfilment_status = "Scheduled"
    add_event(
        db,
        deal,
        "Dispatch scheduled",
        f"Dispatch reference {dispatch.reference}.",
        user.id,
        "Logistics",
    )
    db.commit()
    return serialize(dispatch)


@router.post("/admin/phase5/deals/{deal_id}/complete")
def complete_deal(
    deal_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    deal = db.get(CommercialDeal, deal_id)
    if not deal:
        raise HTTPException(404, "Commercial deal not found")
    if deal.payment_status != "Paid":
        raise HTTPException(409, "Buyer payment must be marked Paid")
    if deal.fulfilment_status != "Delivered":
        raise HTTPException(409, "Delivery must be completed")
    if deal.quality_status not in {"Passed", "Accepted"}:
        raise HTTPException(409, "Quality acceptance is required")

    if not deal.supplier_payment_id:
        payment = SupplierPayment(
            reference=make_reference("SPAY"),
            farmer_id=deal.farmer_id,
            order_id=deal.order_id,
            amount=deal.supplier_amount,
            method="EFT",
            bank_reference=None,
            status="Pending",
            scheduled_date=date.today() + timedelta(days=2),
        )
        db.add(payment)
        db.flush()
        deal.supplier_payment_id = payment.id

    deal.status = "Completed"
    deal.completed_at = datetime.utcnow()
    add_event(
        db,
        deal,
        "Commercial transaction completed",
        f"Gross margin: R {float(deal.gross_margin):,.2f}.",
        user.id,
        "Completion",
    )
    audit(db, user, "Completed commercial deal", "commercial_deal", deal.id)
    db.commit()
    return deal_detail(db, deal)
