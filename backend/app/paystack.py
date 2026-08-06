from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime
from decimal import Decimal
from typing import Literal

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import SessionLocal, get_db
from .funding_models import FundingServiceApplication
from .models import (
    Invoice,
    MembershipApplication,
    Order,
    Payment,
    PaymentTransaction,
)
from .utils import audit, make_reference

router = APIRouter(prefix="/api", tags=["Paystack"])
settings = get_settings()

PAID_MEMBERSHIP_PRICES: dict[str, Decimal] = {
    "Premium Farmer — R99/month": Decimal("99.00"),
    "Premium Buyer — R199/month": Decimal("199.00"),
    "Bronze Marketing — R99": Decimal("99.00"),
    "Silver Marketing — R249": Decimal("249.00"),
    "Gold Marketing — R499": Decimal("499.00"),
}


class PaystackInitializeIn(BaseModel):
    entity_type: Literal["invoice", "order", "membership", "funding_service"]
    entity_id: int = Field(gt=0)
    payer_email: EmailStr
    payer_name: str | None = Field(default=None, max_length=200)


def _paystack_headers() -> dict[str, str]:
    if not settings.paystack_secret_key:
        raise HTTPException(503, "Paystack is not configured")
    return {
        "Authorization": f"Bearer {settings.paystack_secret_key}",
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
    }


def _resolve_charge(
    db: Session,
    entity_type: str,
    entity_id: int,
    submitted_email: str,
    submitted_name: str | None,
) -> tuple[Decimal, str, str]:
    email = submitted_email.strip().lower()

    if entity_type == "invoice":
        invoice = db.get(Invoice, entity_id)
        if not invoice:
            raise HTTPException(404, "Invoice not found")
        if invoice.status == "Paid":
            raise HTTPException(409, "This invoice is already paid")
        if invoice.customer_email and invoice.customer_email.lower() != email:
            raise HTTPException(400, "The email does not match this invoice")
        balance = Decimal(str(invoice.total_amount)) - Decimal(str(invoice.amount_paid or 0))
        if balance <= 0:
            raise HTTPException(409, "This invoice has no outstanding balance")
        return balance, invoice.customer_name, invoice.customer_email or email

    if entity_type == "order":
        order = db.get(Order, entity_id)
        if not order:
            raise HTTPException(404, "Order not found")
        if not order.quoted_amount or Decimal(str(order.quoted_amount)) <= 0:
            raise HTTPException(409, "The order must be formally quoted before payment")
        if order.email and order.email.lower() != email:
            raise HTTPException(400, "The email does not match this order")
        return Decimal(str(order.quoted_amount)), order.business_name, order.email or email

    if entity_type == "funding_service":
        funding_service = db.get(FundingServiceApplication, entity_id)
        if not funding_service:
            raise HTTPException(404, "Funding service registration not found")
        if funding_service.payment_status == "Paid":
            raise HTTPException(409, "This funding service is already paid")
        if funding_service.email.lower() != email:
            raise HTTPException(400, "The email does not match this funding service")
        return (
            Decimal(str(funding_service.service_fee)),
            funding_service.business_name or funding_service.applicant_name,
            funding_service.email,
        )
    membership = db.get(MembershipApplication, entity_id)
    if not membership:
        raise HTTPException(404, "Membership application not found")
    if membership.email.lower() != email:
        raise HTTPException(400, "The email does not match this membership application")
    amount = PAID_MEMBERSHIP_PRICES.get(membership.selected_service)
    if amount is None:
        raise HTTPException(
            409,
            "This service requires a formal quotation or does not require online payment",
        )
    return amount, membership.business_name, membership.email


def _find_or_create_payment(db: Session, tx: PaymentTransaction) -> Payment:
    payment = db.scalar(
        select(Payment).where(Payment.external_reference == tx.reference)
    )
    if payment:
        return payment

    payer_name = tx.payer_email
    if tx.entity_type == "invoice":
        entity = db.get(Invoice, tx.entity_id)
        payer_name = entity.customer_name if entity else payer_name
    elif tx.entity_type == "order":
        entity = db.get(Order, tx.entity_id)
        payer_name = entity.business_name if entity else payer_name
    elif tx.entity_type == "funding_service":
        entity = db.get(FundingServiceApplication, tx.entity_id)
        payer_name = (
            entity.business_name or entity.applicant_name
            if entity
            else payer_name
        )
    elif tx.entity_type == "membership":
        entity = db.get(MembershipApplication, tx.entity_id)
        payer_name = entity.business_name if entity else payer_name

    payment = Payment(
        reference=make_reference("PAY"),
        entity_type=tx.entity_type,
        entity_id=tx.entity_id,
        payer_name=payer_name,
        amount=tx.amount,
        method="Paystack",
        status="Pending",
        external_reference=tx.reference,
        notes="Created automatically from Paystack transaction",
    )
    db.add(payment)
    db.flush()
    return payment


def _apply_success(db: Session, tx: PaymentTransaction, provider_data: dict) -> None:
    payment = _find_or_create_payment(db, tx)
    payment.status = "Paid"
    payment.method = f"Paystack — {provider_data.get('channel') or 'online'}"
    payment.external_reference = tx.reference
    payment.notes = (
        f"Verified Paystack transaction. Gateway response: "
        f"{provider_data.get('gateway_response') or 'Successful'}"
    )

    if tx.entity_type == "invoice":
        invoice = db.get(Invoice, tx.entity_id)
        if invoice:
            invoice.amount_paid = min(
                Decimal(str(invoice.total_amount)),
                Decimal(str(invoice.amount_paid or 0)) + Decimal(str(tx.amount)),
            )
            invoice.status = (
                "Paid"
                if Decimal(str(invoice.amount_paid)) >= Decimal(str(invoice.total_amount))
                else "Part-paid"
            )
    elif tx.entity_type == "membership":
        membership = db.get(MembershipApplication, tx.entity_id)
        if membership and membership.status == "Pending":
            membership.status = "Approved"
            membership.internal_notes = (
                (membership.internal_notes or "")
                + f"\nPaystack payment verified: {tx.reference}"
            ).strip()
    elif tx.entity_type == "funding_service":
        funding_service = db.get(FundingServiceApplication, tx.entity_id)
        if funding_service:
            funding_service.payment_status = "Paid"
            funding_service.payment_method = (
                f"Paystack - {provider_data.get('channel') or 'online'}"
            )
            funding_service.payment_reference = tx.reference
            funding_service.payment_date = datetime.utcnow().date()
            if funding_service.service_status in {
                "Application received",
                "Assessment scheduled",
            }:
                funding_service.service_status = "Ready to commence"
    elif tx.entity_type == "order":
        order = db.get(Order, tx.entity_id)
        if order and order.status in {"Pending", "Approved"}:
            order.status = "In progress"
            order.internal_notes = (
                (order.internal_notes or "")
                + f"\nPaystack payment verified: {tx.reference}"
            ).strip()

    audit(
        db,
        None,
        "Verified Paystack payment",
        tx.entity_type,
        tx.entity_id,
        {
            "reference": tx.reference,
            "amount": float(tx.amount),
            "currency": tx.currency,
            "channel": provider_data.get("channel"),
        },
    )


def _verify_with_paystack(reference: str, db: Session) -> dict:
    tx = db.scalar(
        select(PaymentTransaction).where(PaymentTransaction.reference == reference)
    )
    if not tx:
        raise HTTPException(404, "Transaction not found")

    try:
        with httpx.Client(timeout=30) as client:
            response = client.get(
                f"https://api.paystack.co/transaction/verify/{reference}",
                headers=_paystack_headers(),
            )
        result = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, f"Could not verify the Paystack transaction: {exc}")

    data = result.get("data") or {}
    expected_amount = int(
        (Decimal(str(tx.amount)) * Decimal("100")).quantize(Decimal("1"))
    )
    provider_amount = int(data.get("amount") or 0)
    provider_currency = str(data.get("currency") or "").upper()
    provider_status = str(data.get("status") or "failed").lower()

    success = (
        response.is_success
        and bool(result.get("status"))
        and provider_status == "success"
        and provider_amount == expected_amount
        and provider_currency == tx.currency.upper()
        and str(data.get("reference") or "") == tx.reference
    )

    tx.provider_payload = result
    tx.status = "Paid" if success else provider_status.title()
    if success and not tx.verified_at:
        tx.verified_at = datetime.utcnow()
        _apply_success(db, tx, data)
    elif not success:
        payment = _find_or_create_payment(db, tx)
        payment.status = "Failed" if provider_status in {"failed", "abandoned"} else "Pending"

    db.commit()
    return {
        "verified": success,
        "reference": tx.reference,
        "status": tx.status,
        "amount": float(tx.amount),
        "currency": tx.currency,
        "paid_at": data.get("paid_at"),
        "channel": data.get("channel"),
        "gateway_response": data.get("gateway_response"),
    }


def _background_verify(reference: str) -> None:
    with SessionLocal() as db:
        try:
            _verify_with_paystack(reference, db)
        except Exception:
            db.rollback()


@router.post("/payments/paystack/initialize", status_code=201)
def initialize_paystack(
    data: PaystackInitializeIn,
    request: Request,
    db: Session = Depends(get_db),
):
    amount, payer_name, payer_email = _resolve_charge(
        db,
        data.entity_type,
        data.entity_id,
        str(data.payer_email),
        data.payer_name,
    )

    # A fresh unique reference is mandatory for every Paystack initialization.
    reference = make_reference("PSTK")
    callback_url = settings.paystack_callback_url or (
        settings.public_base_url.rstrip("/") + "/payment-success.html"
    )

    channels = [
        item.strip()
        for item in settings.paystack_channels.split(",")
        if item.strip()
    ]

    payload = {
        "email": payer_email,
        "amount": str(
            int((amount * Decimal("100")).quantize(Decimal("1")))
        ),
        "currency": "ZAR",
        "reference": reference,
        "callback_url": callback_url,
        "metadata": json.dumps(
            {
                "entity_type": data.entity_type,
                "entity_id": data.entity_id,
                "payer_name": payer_name,
                "source": "FarmLink Distribution",
            }
        ),
    }
    if channels:
        payload["channels"] = channels

    try:
        with httpx.Client(timeout=30) as client:
            response = client.post(
                "https://api.paystack.co/transaction/initialize",
                json=payload,
                headers=_paystack_headers(),
            )
        result = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, f"Could not initialize Paystack: {exc}")

    if not response.is_success or not result.get("status"):
        raise HTTPException(
            502,
            result.get("message") or "Paystack initialization failed",
        )

    result_data = result.get("data") or {}
    tx = PaymentTransaction(
        reference=reference,
        provider="Paystack",
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        payer_email=payer_email,
        amount=amount,
        currency="ZAR",
        status="Initialized",
        authorization_url=result_data.get("authorization_url"),
        provider_payload=result,
    )
    db.add(tx)
    db.flush()
    _find_or_create_payment(db, tx)
    audit(
        db,
        None,
        "Initialized Paystack payment",
        data.entity_type,
        data.entity_id,
        {
            "reference": reference,
            "amount": float(amount),
            "ip": request.client.host if request.client else None,
        },
        request.client.host if request.client else None,
    )
    db.commit()

    return {
        "reference": reference,
        "authorization_url": tx.authorization_url,
        "amount": float(amount),
        "currency": "ZAR",
    }


@router.get("/payments/paystack/verify/{reference}")
def verify_paystack(reference: str, db: Session = Depends(get_db)):
    return _verify_with_paystack(reference, db)


@router.get("/payments/paystack/status/{reference}")
def payment_status(reference: str, db: Session = Depends(get_db)):
    tx = db.scalar(
        select(PaymentTransaction).where(PaymentTransaction.reference == reference)
    )
    if not tx:
        raise HTTPException(404, "Transaction not found")
    return {
        "reference": tx.reference,
        "status": tx.status,
        "verified": bool(tx.verified_at),
        "amount": float(tx.amount),
        "currency": tx.currency,
        "created_at": tx.created_at,
        "verified_at": tx.verified_at,
    }


@router.post("/payments/paystack/webhook")
async def paystack_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    raw_body = await request.body()
    signature = request.headers.get("x-paystack-signature", "")
    if not settings.paystack_secret_key:
        raise HTTPException(503, "Paystack is not configured")

    expected = hmac.new(
        settings.paystack_secret_key.encode("utf-8"),
        raw_body,
        hashlib.sha512,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        raise HTTPException(401, "Invalid webhook signature")

    try:
        event = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid webhook payload")

    if event.get("event") == "charge.success":
        reference = str((event.get("data") or {}).get("reference") or "")
        if reference:
            # Return 200 immediately and perform server-side verification in the background.
            background_tasks.add_task(_background_verify, reference)

    return {"received": True}
