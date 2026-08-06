from __future__ import annotations

import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import desc, func, or_, select
from sqlalchemy.orm import Session

from .database import get_db
from .deps import current_user
from .models import Buyer, EntrepreneurshipApplication, Farmer, Notification, User
from .phase3_models import EntrepreneurWorkspace
from .phase4_models import (
    BuyerRequirement,
    MarketplaceListing,
    SupplierActivationProfile,
    SupplierBuyerMatch,
)
from .phase4_schemas import (
    BuyerRequirementCreate,
    BuyerRequirementUpdate,
    FarmerConversionCreate,
    MarketplaceListingCreate,
    MarketplaceListingUpdate,
    MatchUpdate,
    SupplierActivationUpdate,
)
from .utils import audit, make_reference


router = APIRouter(prefix="/api", tags=["AgriStart Phase 4"])


def serialize(record) -> dict:
    result = {
        column.name: getattr(record, column.name)
        for column in record.__table__.columns
    }
    if "unit_price" in result and result["unit_price"] is not None:
        result["unit_price"] = float(result["unit_price"])
    return result


def get_applicant(db: Session, entrepreneur_id: int) -> EntrepreneurshipApplication:
    applicant = db.get(EntrepreneurshipApplication, entrepreneur_id)
    if not applicant:
        raise HTTPException(404, "AgriStart applicant not found")
    return applicant


def get_workspace(db: Session, entrepreneur_id: int) -> EntrepreneurWorkspace | None:
    return db.scalar(
        select(EntrepreneurWorkspace).where(
            EntrepreneurWorkspace.entrepreneur_id == entrepreneur_id
        )
    )


def get_or_create_activation(
    db: Session, entrepreneur_id: int
) -> SupplierActivationProfile:
    activation = db.scalar(
        select(SupplierActivationProfile).where(
            SupplierActivationProfile.entrepreneur_id == entrepreneur_id
        )
    )
    if activation:
        return activation
    get_applicant(db, entrepreneur_id)
    activation = SupplierActivationProfile(entrepreneur_id=entrepreneur_id)
    db.add(activation)
    db.flush()
    return activation


def normalized_tokens(value: str | None) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", (value or "").lower())
        if len(token) > 2
    }


def text_overlap_score(supplier_text: str, buyer_text: str, maximum: int) -> int:
    supplier_tokens = normalized_tokens(supplier_text)
    buyer_tokens = normalized_tokens(buyer_text)
    if not supplier_tokens or not buyer_tokens:
        return 0
    overlap = len(supplier_tokens & buyer_tokens)
    denominator = max(1, min(len(supplier_tokens), len(buyer_tokens)))
    return min(maximum, round(overlap / denominator * maximum))


def location_score(supplier_location: str, buyer_location: str) -> int:
    supplier = normalized_tokens(supplier_location)
    buyer = normalized_tokens(buyer_location)
    if not supplier or not buyer:
        return 0
    if supplier == buyer:
        return 20
    if supplier & buyer:
        return 14
    return 0


def capacity_score(capacity: int, minimum: int) -> int:
    if minimum <= 0:
        return 15
    if capacity >= minimum:
        return 15
    return max(0, round(capacity / minimum * 15))


def calculate_match(
    listing: MarketplaceListing,
    requirement: BuyerRequirement,
) -> dict:
    product = text_overlap_score(
        f"{listing.product_name} {listing.product_category} {listing.description}",
        f"{requirement.product_category} {requirement.product_description}",
        35,
    )
    location = location_score(listing.location, requirement.location)
    capacity = capacity_score(
        listing.weekly_capacity,
        requirement.minimum_weekly_capacity,
    )
    packaging = text_overlap_score(
        listing.packaging or "",
        requirement.packaging_required or "",
        15,
    )
    if not requirement.packaging_required:
        packaging = 15
    delivery = (
        15
        if not requirement.delivery_required
        or "yes" in listing.delivery_capability.lower()
        or "deliver" in listing.delivery_capability.lower()
        else 0
    )
    total = product + location + capacity + packaging + delivery
    reasons = []
    if product >= 20:
        reasons.append("Strong product alignment")
    if location:
        reasons.append("Location alignment")
    if capacity == 15:
        reasons.append("Capacity requirement met")
    if packaging == 15:
        reasons.append("Packaging aligned")
    if delivery == 15:
        reasons.append("Delivery requirement aligned")
    return {
        "match_score": min(100, total),
        "product_score": product,
        "location_score": location,
        "capacity_score": capacity,
        "packaging_score": packaging,
        "delivery_score": delivery,
        "match_reasons": ", ".join(reasons) or "Manual review recommended",
    }


def activation_row(db: Session, applicant: EntrepreneurshipApplication) -> dict:
    activation = get_or_create_activation(db, applicant.id)
    workspace = get_workspace(db, applicant.id)
    farmer = db.get(Farmer, activation.farmer_id) if activation.farmer_id else None
    listings = db.scalar(
        select(func.count())
        .select_from(MarketplaceListing)
        .where(MarketplaceListing.entrepreneur_id == applicant.id)
    ) or 0
    matches = db.scalar(
        select(func.count())
        .select_from(SupplierBuyerMatch)
        .where(SupplierBuyerMatch.entrepreneur_id == applicant.id)
    ) or 0
    return {
        "entrepreneur_id": applicant.id,
        "reference": applicant.reference,
        "full_name": applicant.full_name,
        "email": applicant.email,
        "phone": applicant.phone,
        "province": applicant.province,
        "municipality": applicant.municipality,
        "agricultural_interest": applicant.agricultural_interest,
        "business_idea": applicant.business_idea,
        "workspace": serialize(workspace) if workspace else None,
        "activation": serialize(activation),
        "farmer": serialize(farmer) if farmer else None,
        "listing_count": listings,
        "match_count": matches,
    }


@router.get("/admin/phase4/dashboard")
def phase4_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    applicants = db.scalars(
        select(EntrepreneurshipApplication).order_by(
            desc(EntrepreneurshipApplication.created_at)
        )
    ).all()
    rows = [activation_row(db, applicant) for applicant in applicants]
    db.commit()
    return {
        "summary": {
            "candidates": len(rows),
            "verified": sum(
                1
                for row in rows
                if row["activation"]["verification_status"] == "Verified"
            ),
            "activated": sum(
                1 for row in rows if row["activation"]["farmer_id"] is not None
            ),
            "published_listings": db.scalar(
                select(func.count())
                .select_from(MarketplaceListing)
                .where(MarketplaceListing.status == "Published")
            ) or 0,
            "open_requirements": db.scalar(
                select(func.count())
                .select_from(BuyerRequirement)
                .where(BuyerRequirement.status == "Open")
            ) or 0,
            "active_matches": db.scalar(
                select(func.count())
                .select_from(SupplierBuyerMatch)
                .where(
                    SupplierBuyerMatch.status.in_(
                        ["Suggested", "Shortlisted", "Introduced", "Negotiating"]
                    )
                )
            ) or 0,
        },
        "items": rows,
    }


@router.get("/admin/phase4/entrepreneurs/{entrepreneur_id}")
def phase4_entrepreneur_detail(
    entrepreneur_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    applicant = get_applicant(db, entrepreneur_id)
    row = activation_row(db, applicant)
    row["listings"] = [
        serialize(item)
        for item in db.scalars(
            select(MarketplaceListing)
            .where(MarketplaceListing.entrepreneur_id == entrepreneur_id)
            .order_by(desc(MarketplaceListing.created_at))
        ).all()
    ]
    row["matches"] = [
        serialize(item)
        for item in db.scalars(
            select(SupplierBuyerMatch)
            .where(SupplierBuyerMatch.entrepreneur_id == entrepreneur_id)
            .order_by(desc(SupplierBuyerMatch.match_score))
        ).all()
    ]
    db.commit()
    return row


@router.patch("/admin/phase4/entrepreneurs/{entrepreneur_id}/activation")
def update_activation(
    entrepreneur_id: int,
    data: SupplierActivationUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    activation = get_or_create_activation(db, entrepreneur_id)
    values = data.model_dump(exclude_unset=True)
    for field, value in values.items():
        setattr(activation, field, value)
    if values.get("verification_status") == "Verified":
        activation.verified_by_id = user.id
        activation.verified_at = datetime.utcnow()
    audit(
        db,
        user,
        "Updated supplier activation",
        "supplier_activation",
        activation.id,
        values,
        request.client.host if request.client else None,
    )
    db.commit()
    return serialize(activation)


@router.post(
    "/admin/phase4/entrepreneurs/{entrepreneur_id}/convert-to-farmer",
    status_code=201,
)
def convert_to_farmer(
    entrepreneur_id: int,
    data: FarmerConversionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    applicant = get_applicant(db, entrepreneur_id)
    activation = get_or_create_activation(db, entrepreneur_id)
    if activation.farmer_id:
        raise HTTPException(409, "This entrepreneur is already linked to a farmer")

    if activation.verification_status != "Verified":
        raise HTTPException(
            409,
            "Supplier verification must be completed before farmer activation",
        )

    farmer = Farmer(
        reference=make_reference("FAR"),
        farm_name=data.farm_name,
        contact_person=applicant.full_name,
        phone=applicant.phone,
        email=applicant.email,
        location=data.location,
        producer_type=data.producer_type,
        weekly_capacity=data.weekly_capacity,
        egg_sizes=data.egg_sizes,
        packaging=data.packaging,
        delivery_capability=data.delivery_capability,
        notes=data.notes,
        membership_plan="Standard Farmer - Free",
        status="Approved",
        assigned_to_id=applicant.assigned_to_id,
        internal_notes=(
            f"Activated from AgriStart {applicant.reference}. "
            "Phase 4 supplier activation completed."
        ),
    )
    db.add(farmer)
    db.flush()

    activation.farmer_id = farmer.id
    activation.activation_status = "Activated"
    activation.marketplace_enabled = True
    activation.buyer_matching_enabled = True
    activation.activated_at = datetime.utcnow()

    workspace = get_workspace(db, entrepreneur_id)
    if workspace:
        workspace.supplier_verification_status = "Verified"
        workspace.marketplace_status = "Ready"
        workspace.launch_status = (
            "Launched"
            if workspace.first_sale_completed or workspace.production_started
            else "Launch ready"
        )
        workspace.next_action = "Create marketplace listing and run buyer matching"

    audit(
        db,
        user,
        "Converted AgriStart entrepreneur to approved farmer",
        "farmer",
        farmer.id,
        {
            "farmer_reference": farmer.reference,
            "entrepreneur_reference": applicant.reference,
        },
    )
    db.commit()
    return {
        "farmer": serialize(farmer),
        "activation": serialize(activation),
    }


@router.get("/admin/phase4/buyer-requirements")
def buyer_requirements(
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    statement = select(BuyerRequirement)
    if status and status != "all":
        statement = statement.where(BuyerRequirement.status == status)
    rows = db.scalars(
        statement.order_by(desc(BuyerRequirement.created_at))
    ).all()
    result = []
    for row in rows:
        item = serialize(row)
        buyer = db.get(Buyer, row.buyer_id)
        item["buyer"] = serialize(buyer) if buyer else None
        result.append(item)
    return result


@router.post("/admin/phase4/buyer-requirements", status_code=201)
def create_buyer_requirement(
    data: BuyerRequirementCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    buyer = db.get(Buyer, data.buyer_id)
    if not buyer:
        raise HTTPException(404, "Buyer not found")
    requirement = BuyerRequirement(
        reference=make_reference("REQ"),
        created_by_id=user.id,
        **data.model_dump(),
    )
    db.add(requirement)
    db.flush()
    audit(
        db,
        user,
        "Created buyer requirement",
        "buyer_requirement",
        requirement.id,
    )
    db.commit()
    return serialize(requirement)


@router.patch("/admin/phase4/buyer-requirements/{requirement_id}")
def update_buyer_requirement(
    requirement_id: int,
    data: BuyerRequirementUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    requirement = db.get(BuyerRequirement, requirement_id)
    if not requirement:
        raise HTTPException(404, "Buyer requirement not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(requirement, field, value)
    audit(
        db,
        user,
        "Updated buyer requirement",
        "buyer_requirement",
        requirement.id,
    )
    db.commit()
    return serialize(requirement)


@router.get("/admin/phase4/listings")
def admin_listings(
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    statement = select(MarketplaceListing)
    if status and status != "all":
        statement = statement.where(MarketplaceListing.status == status)
    return [
        serialize(item)
        for item in db.scalars(
            statement.order_by(desc(MarketplaceListing.created_at))
        ).all()
    ]


@router.post("/admin/phase4/listings", status_code=201)
def create_listing(
    data: MarketplaceListingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    applicant = get_applicant(db, data.entrepreneur_id)
    activation = get_or_create_activation(db, data.entrepreneur_id)
    if not activation.farmer_id:
        raise HTTPException(409, "Activate the entrepreneur as a farmer first")
    if activation.verification_status != "Verified":
        raise HTTPException(409, "Supplier must be verified before listing")

    farmer = db.get(Farmer, activation.farmer_id)
    listing = MarketplaceListing(
        reference=make_reference("LST"),
        farmer_id=activation.farmer_id,
        business_name=farmer.farm_name if farmer else applicant.full_name,
        **data.model_dump(),
    )
    if listing.status == "Published":
        listing.published_at = datetime.utcnow()
    db.add(listing)
    db.flush()

    activation.marketplace_enabled = True
    workspace = get_workspace(db, data.entrepreneur_id)
    if workspace:
        workspace.marketplace_status = (
            "Published" if listing.status == "Published" else "Ready"
        )

    audit(db, user, "Created marketplace listing", "marketplace_listing", listing.id)
    db.commit()
    return serialize(listing)


@router.patch("/admin/phase4/listings/{listing_id}")
def update_listing(
    listing_id: int,
    data: MarketplaceListingUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    listing = db.get(MarketplaceListing, listing_id)
    if not listing:
        raise HTTPException(404, "Marketplace listing not found")
    values = data.model_dump(exclude_unset=True)
    for field, value in values.items():
        setattr(listing, field, value)
    if values.get("status") == "Published" and not listing.published_at:
        listing.published_at = datetime.utcnow()
    audit(db, user, "Updated marketplace listing", "marketplace_listing", listing.id)
    db.commit()
    return serialize(listing)


@router.post("/admin/phase4/matching/run")
def run_matching(
    minimum_score: int = 40,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    listings = db.scalars(
        select(MarketplaceListing).where(
            MarketplaceListing.status == "Published"
        )
    ).all()
    requirements = db.scalars(
        select(BuyerRequirement).where(BuyerRequirement.status == "Open")
    ).all()

    created = 0
    updated = 0
    for listing in listings:
        activation = get_or_create_activation(db, listing.entrepreneur_id)
        if not activation.buyer_matching_enabled:
            continue
        for requirement in requirements:
            score = calculate_match(listing, requirement)
            if score["match_score"] < minimum_score:
                continue
            match = db.scalar(
                select(SupplierBuyerMatch).where(
                    SupplierBuyerMatch.entrepreneur_id == listing.entrepreneur_id,
                    SupplierBuyerMatch.buyer_requirement_id == requirement.id,
                )
            )
            if not match:
                match = SupplierBuyerMatch(
                    reference=make_reference("MAT"),
                    entrepreneur_id=listing.entrepreneur_id,
                    farmer_id=listing.farmer_id,
                    buyer_requirement_id=requirement.id,
                    **score,
                )
                db.add(match)
                created += 1
            elif match.status == "Suggested":
                for field, value in score.items():
                    setattr(match, field, value)
                updated += 1

    audit(
        db,
        user,
        "Ran supplier buyer matching",
        "supplier_match",
        None,
        {
            "created": created,
            "updated": updated,
            "minimum_score": minimum_score,
        },
    )
    db.commit()
    return {"created": created, "updated": updated}


@router.get("/admin/phase4/matches")
def matches(
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    statement = select(SupplierBuyerMatch)
    if status and status != "all":
        statement = statement.where(SupplierBuyerMatch.status == status)
    rows = db.scalars(
        statement.order_by(desc(SupplierBuyerMatch.match_score))
    ).all()
    result = []
    for row in rows:
        item = serialize(row)
        applicant = db.get(EntrepreneurshipApplication, row.entrepreneur_id)
        farmer = db.get(Farmer, row.farmer_id) if row.farmer_id else None
        requirement = db.get(BuyerRequirement, row.buyer_requirement_id)
        buyer = db.get(Buyer, requirement.buyer_id) if requirement else None
        item["supplier_name"] = (
            farmer.farm_name if farmer else applicant.full_name if applicant else None
        )
        item["requirement"] = serialize(requirement) if requirement else None
        item["buyer"] = serialize(buyer) if buyer else None
        result.append(item)
    return result


@router.patch("/admin/phase4/matches/{match_id}")
def update_match(
    match_id: int,
    data: MatchUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    match = db.get(SupplierBuyerMatch, match_id)
    if not match:
        raise HTTPException(404, "Supplier match not found")
    values = data.model_dump(exclude_unset=True)
    for field, value in values.items():
        setattr(match, field, value)
    if values.get("status") == "Introduced" and not match.introduced_at:
        match.introduced_at = datetime.utcnow()

        requirement = db.get(BuyerRequirement, match.buyer_requirement_id)
        buyer = db.get(Buyer, requirement.buyer_id) if requirement else None
        farmer = db.get(Farmer, match.farmer_id) if match.farmer_id else None
        applicant = db.get(EntrepreneurshipApplication, match.entrepreneur_id)

        if buyer:
            db.add(
                Notification(
                    channel="Email",
                    recipient=buyer.email,
                    subject=f"FarmLink supplier match {match.reference}",
                    message=(
                        f"Dear {buyer.contact_person},\n\n"
                        f"FarmLink has identified a supplier match for "
                        f"{requirement.product_category}. "
                        f"Match score: {match.match_score}%.\n\n"
                        "A FarmLink administrator will coordinate the introduction."
                    ),
                    status="Queued",
                )
            )
        if applicant and applicant.email:
            db.add(
                Notification(
                    channel="Email",
                    recipient=applicant.email,
                    subject=f"FarmLink buyer opportunity {match.reference}",
                    message=(
                        f"Dear {applicant.full_name},\n\n"
                        "Your business has been matched to a buyer requirement. "
                        f"Match score: {match.match_score}%.\n\n"
                        "FarmLink will coordinate the next steps."
                    ),
                    status="Queued",
                )
            )

    audit(db, user, "Updated supplier buyer match", "supplier_match", match.id)
    db.commit()
    return serialize(match)


@router.get("/public/phase4/suppliers")
def public_suppliers(
    q: str | None = None,
    location: str | None = None,
    category: str | None = None,
    limit: int = 24,
    db: Session = Depends(get_db),
):
    statement = select(MarketplaceListing).where(
        MarketplaceListing.status == "Published"
    )
    if q:
        term = f"%{q.strip()}%"
        statement = statement.where(
            or_(
                MarketplaceListing.product_name.ilike(term),
                MarketplaceListing.product_category.ilike(term),
                MarketplaceListing.description.ilike(term),
                MarketplaceListing.business_name.ilike(term),
            )
        )
    if location:
        statement = statement.where(
            MarketplaceListing.location.ilike(f"%{location.strip()}%")
        )
    if category:
        statement = statement.where(
            MarketplaceListing.product_category.ilike(f"%{category.strip()}%")
        )

    rows = db.scalars(
        statement.order_by(
            desc(MarketplaceListing.featured),
            desc(MarketplaceListing.published_at),
        ).limit(min(max(limit, 1), 48))
    ).all()

    return [
        {
            "reference": row.reference,
            "business_name": row.business_name,
            "product_name": row.product_name,
            "product_category": row.product_category,
            "description": row.description,
            "location": row.location,
            "weekly_capacity": row.weekly_capacity,
            "packaging": row.packaging,
            "delivery_capability": row.delivery_capability,
            "minimum_order": row.minimum_order,
            "unit_price": float(row.unit_price) if row.unit_price is not None else None,
            "featured": row.featured,
        }
        for row in rows
    ]
