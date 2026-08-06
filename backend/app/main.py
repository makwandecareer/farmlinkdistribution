from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Type
from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func, or_, desc
from sqlalchemy.orm import Session
from .config import get_settings
from .database import Base, engine, get_db, SessionLocal
from .models import User, UserRole, Farmer, Buyer, Order, MembershipApplication, EntrepreneurshipApplication, Payment, AuditLog, LoginAttempt, InventoryLot
from .schemas import LoginIn, ChangePasswordIn, UserCreate, UserUpdate, UserPasswordReset, UserOut, TokenOut, FarmerCreate, BuyerCreate, OrderCreate, MembershipCreate, EntrepreneurshipCreate, RecordUpdate, PaymentCreate, PaymentUpdate
from .security import hash_password, verify_password, create_access_token
from .deps import current_user, ceo_user
from .utils import make_reference, audit
from .operations import router as operations_router
from .phase3_routes import router as phase3_router
from .phase4_routes import router as phase4_router
from .funding_routes import router as funding_router
from .paystack import router as paystack_router

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    if settings.initial_ceo_email and settings.initial_ceo_password:
        with SessionLocal() as db:
            if not db.scalar(select(User).where(User.email == settings.initial_ceo_email.lower())):
                db.add(User(full_name=settings.initial_ceo_name, email=settings.initial_ceo_email.lower(), password_hash=hash_password(settings.initial_ceo_password), role=UserRole.CEO.value, job_title="Founder & Chief Executive Officer", must_change_password=True))
                db.commit()
    yield

app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
PRODUCTION_CORS_ORIGINS = {
    "https://www.farmlinkdistribution.co.za",
    "https://farmlinkdistribution.co.za",
    "https://farmlinkdistribution-1ndv.onrender.com",
    "https://farmlinkdistribution-web.onrender.com",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
}

configured_origins = {
    str(origin).strip().rstrip("/")
    for origin in (settings.cors_origin_list or [])
    if str(origin).strip()
}

allowed_origins = sorted(PRODUCTION_CORS_ORIGINS | configured_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://farmlinkdistribution(?:-[a-z0-9]+)?\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
app.include_router(operations_router)
app.include_router(phase3_router)
app.include_router(phase4_router)
app.include_router(funding_router)
app.include_router(paystack_router)

@app.get("/api/health")
def health(): return {"status":"ok","service":settings.app_name,"environment":settings.environment}

@app.post("/api/auth/login", response_model=TokenOut)
def login(data: LoginIn, request: Request, db: Session = Depends(get_db)):
    email=data.email.lower(); ip=request.client.host if request.client else None; cutoff=datetime.utcnow()-timedelta(minutes=15)
    failures=db.scalar(select(func.count()).select_from(LoginAttempt).where(LoginAttempt.email==email,LoginAttempt.successful==False,LoginAttempt.created_at>=cutoff)) or 0
    if failures >= 5: raise HTTPException(429,"Too many failed sign-in attempts. Try again after 15 minutes.")
    user = db.scalar(select(User).where(User.email == email))
    success=bool(user and user.is_active and verify_password(data.password, user.password_hash))
    db.add(LoginAttempt(email=email,ip_address=ip,successful=success))
    if not success:
        db.commit(); raise HTTPException(401, "Invalid email or password")
    user.last_login_at = datetime.utcnow(); audit(db,user,"Signed in","user",user.id,ip=ip); db.commit(); db.refresh(user)
    return TokenOut(access_token=create_access_token(str(user.id), user.role), user=user)

@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)): return user

@app.post("/api/auth/change-password")
def change_password(data: ChangePasswordIn, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not verify_password(data.current_password, user.password_hash): raise HTTPException(400,"Current password is incorrect")
    user.password_hash=hash_password(data.new_password); user.must_change_password=False; audit(db,user,"Changed password","user",user.id); db.commit(); return {"message":"Password updated"}

@app.post("/api/public/farmers", status_code=201)
def create_farmer(data: FarmerCreate, request: Request, db: Session=Depends(get_db)):
    rec=Farmer(reference=make_reference("FAR"), **data.model_dump()); db.add(rec); db.flush(); audit(db,None,"Submitted farmer registration","farmer",rec.id,{"reference":rec.reference},request.client.host if request.client else None); db.commit(); return {"id":rec.id,"reference":rec.reference,"status":rec.status}

@app.post("/api/public/buyers", status_code=201)
def create_buyer(data: BuyerCreate, request: Request, db: Session=Depends(get_db)):
    rec=Buyer(reference=make_reference("BUY"), **data.model_dump()); db.add(rec); db.flush(); audit(db,None,"Submitted buyer registration","buyer",rec.id,{"reference":rec.reference},request.client.host if request.client else None); db.commit(); return {"id":rec.id,"reference":rec.reference,"status":rec.status}

@app.post("/api/public/orders", status_code=201)
def create_order(data: OrderCreate, request: Request, db: Session=Depends(get_db)):
    rec=Order(reference=make_reference("ORD"), **data.model_dump()); db.add(rec); db.flush(); audit(db,None,"Submitted bulk order","order",rec.id,{"reference":rec.reference},request.client.host if request.client else None); db.commit(); return {"id":rec.id,"reference":rec.reference,"status":rec.status}

@app.post("/api/public/memberships", status_code=201)
def create_membership(data: MembershipCreate, request: Request, db: Session=Depends(get_db)):
    rec=MembershipApplication(reference=make_reference("MEM"), **data.model_dump()); db.add(rec); db.flush(); audit(db,None,"Submitted membership application","membership",rec.id,{"reference":rec.reference},request.client.host if request.client else None); db.commit(); return {"id":rec.id,"reference":rec.reference,"status":rec.status}
@app.post("/api/public/entrepreneurs", status_code=201)
def create_entrepreneurship_application(data: EntrepreneurshipCreate, request: Request, db: Session=Depends(get_db)):
    rec=EntrepreneurshipApplication(reference=make_reference("AGR"), **data.model_dump())
    db.add(rec); db.flush()
    audit(db,None,"Submitted agricultural entrepreneurship application","entrepreneur",rec.id,{"reference":rec.reference},request.client.host if request.client else None)
    db.commit()
    return {"id":rec.id,"reference":rec.reference,"status":rec.status}

MODEL_MAP={"farmers":Farmer,"buyers":Buyer,"orders":Order,"memberships":MembershipApplication,"entrepreneurs":EntrepreneurshipApplication}

def serialize(rec):
    out={c.name:getattr(rec,c.name) for c in rec.__table__.columns}
    if hasattr(rec,"assigned_to") and rec.assigned_to: out["assigned_to"]={"id":rec.assigned_to.id,"full_name":rec.assigned_to.full_name}
    return out

@app.get("/api/admin/dashboard")
def dashboard(db: Session=Depends(get_db), user: User=Depends(current_user)):
    counts={}
    for key,model in MODEL_MAP.items():
        counts[key]={"total":db.scalar(select(func.count()).select_from(model)) or 0,"pending":db.scalar(select(func.count()).select_from(model).where(model.status=="Pending")) or 0}
    counts["open_orders"]=db.scalar(select(func.count()).select_from(Order).where(Order.status.in_(["Pending","Approved","In progress"]))) or 0
    counts["completed"]=sum(db.scalar(select(func.count()).select_from(m).where(m.status.in_(["Approved","Completed"]))) or 0 for m in MODEL_MAP.values())
    latest=[]
    for typ,m in MODEL_MAP.items():
        for r in db.scalars(select(m).order_by(desc(m.created_at)).limit(5)):
            latest.append({"type":typ[:-1], **serialize(r)})
    latest=sorted(latest,key=lambda x:x["created_at"],reverse=True)[:10]
    return {"counts":counts,"latest":latest}

# IMPORTANT: Keep administrator routes above the generic
# /api/admin/{resource} route. Starlette resolves routes in declaration order;
# otherwise "/api/admin/users" is captured as resource="users" and returns 404.
@app.get("/api/admin/users")
def users(db:Session=Depends(get_db), user:User=Depends(current_user)):
    rows=db.scalars(select(User).order_by(User.full_name)).all()
    result=[]
    for u in rows:
        created_log=db.scalar(
            select(AuditLog).where(
                AuditLog.entity_type=="user",
                AuditLog.entity_id==u.id,
                AuditLog.action=="Created administrator"
            ).order_by(AuditLog.created_at)
        )
        latest_log=db.scalar(
            select(AuditLog).where(
                or_(AuditLog.actor_id==u.id,
                    ((AuditLog.entity_type=="user") & (AuditLog.entity_id==u.id)))
            ).order_by(desc(AuditLog.created_at))
        )
        item={c.name:getattr(u,c.name) for c in u.__table__.columns if c.name!="password_hash"}
        item["created_by"]=created_log.actor_name if created_log else ("System" if u.role==UserRole.CEO.value else "Not recorded")
        item["last_activity"]=latest_log.action if latest_log else ("Signed in" if u.last_login_at else "No activity")
        item["last_activity_at"]=latest_log.created_at if latest_log else u.last_login_at
        result.append(item)
    return result

@app.post("/api/admin/users", response_model=UserOut, status_code=201)
def create_user(data:UserCreate, db:Session=Depends(get_db), ceo:User=Depends(ceo_user)):
    if db.scalar(select(User).where(User.email==data.email.lower())): raise HTTPException(409,"Email already exists")
    u=User(full_name=data.full_name,email=data.email.lower(),job_title=data.job_title,password_hash=hash_password(data.temporary_password),role=data.role,must_change_password=True)
    db.add(u); db.flush(); audit(db,ceo,"Created administrator","user",u.id,{"email":u.email}); db.commit(); db.refresh(u); return u


@app.get("/api/admin/users/{user_id}", response_model=UserOut)
def user_detail(user_id:int, db:Session=Depends(get_db), ceo:User=Depends(ceo_user)):
    u=db.get(User,user_id)
    if not u: raise HTTPException(404,"Administrator not found")
    return u

@app.patch("/api/admin/users/{user_id}", response_model=UserOut)
def update_user(user_id:int, data:UserUpdate, db:Session=Depends(get_db), ceo:User=Depends(ceo_user)):
    u=db.get(User,user_id)
    if not u: raise HTTPException(404,"Administrator not found")
    duplicate=db.scalar(select(User).where(User.email==data.email.lower(),User.id!=user_id))
    if duplicate: raise HTTPException(409,"Email already exists")
    if u.role==UserRole.CEO.value and data.role!=UserRole.CEO.value:
        raise HTTPException(400,"The protected CEO role cannot be changed")
    if u.role!=UserRole.CEO.value and data.role==UserRole.CEO.value:
        raise HTTPException(400,"A second CEO account cannot be assigned")
    before={"full_name":u.full_name,"email":u.email,"job_title":u.job_title,"role":u.role}
    u.full_name=data.full_name.strip()
    u.email=data.email.lower()
    u.job_title=data.job_title.strip()
    if u.role!=UserRole.CEO.value:
        u.role=data.role
    audit(db,ceo,"Updated administrator","user",u.id,{"before":before,"after":{"full_name":u.full_name,"email":u.email,"job_title":u.job_title,"role":u.role}})
    db.commit(); db.refresh(u); return u

@app.post("/api/admin/users/{user_id}/reset-password", response_model=UserOut)
def reset_user_password(user_id:int, data:UserPasswordReset, db:Session=Depends(get_db), ceo:User=Depends(ceo_user)):
    u=db.get(User,user_id)
    if not u: raise HTTPException(404,"Administrator not found")
    if u.role==UserRole.CEO.value and u.id!=ceo.id:
        raise HTTPException(400,"Another CEO account cannot be reset")
    u.password_hash=hash_password(data.temporary_password)
    u.must_change_password=True
    audit(db,ceo,"Reset administrator password","user",u.id,{"email":u.email})
    db.commit(); db.refresh(u); return u

@app.get("/api/admin/users/{user_id}/audit")
def user_audit(user_id:int, limit:int=Query(100,le=500), db:Session=Depends(get_db), ceo:User=Depends(ceo_user)):
    u=db.get(User,user_id)
    if not u: raise HTTPException(404,"Administrator not found")
    rows=db.scalars(
        select(AuditLog).where(
            or_(
                AuditLog.actor_id==user_id,
                ((AuditLog.entity_type=="user") & (AuditLog.entity_id==user_id))
            )
        ).order_by(desc(AuditLog.created_at)).limit(limit)
    ).all()
    return [{c.name:getattr(r,c.name) for c in r.__table__.columns} for r in rows]

@app.patch("/api/admin/users/{user_id}/status", response_model=UserOut)
def user_status(user_id:int, active:bool, db:Session=Depends(get_db), ceo:User=Depends(ceo_user)):
    u=db.get(User,user_id)
    if not u: raise HTTPException(404,"Administrator not found")
    if u.role==UserRole.CEO.value: raise HTTPException(400,"CEO account cannot be suspended")
    u.is_active=active; audit(db,ceo,"Activated administrator" if active else "Suspended administrator","user",u.id); db.commit(); db.refresh(u); return u

@app.delete("/api/admin/users/{user_id}", status_code=204)
def delete_user(user_id:int, db:Session=Depends(get_db), ceo:User=Depends(ceo_user)):
    u=db.get(User,user_id)
    if not u: raise HTTPException(404,"Administrator not found")
    if u.role==UserRole.CEO.value: raise HTTPException(400,"CEO account cannot be removed")

    assigned_records=0
    for model in MODEL_MAP.values():
        if hasattr(model,"assigned_to_id"):
            assigned_records += db.scalar(
                select(func.count()).select_from(model).where(model.assigned_to_id==user_id)
            ) or 0
    historical_actions=db.scalar(
        select(func.count()).select_from(AuditLog).where(AuditLog.actor_id==user_id)
    ) or 0

    if assigned_records or historical_actions:
        raise HTTPException(
            409,
            "This administrator has operational or audit history and cannot be deleted. Suspend the account to preserve governance records."
        )

    audit(db,ceo,"Removed administrator","user",u.id,{"email":u.email})
    db.delete(u); db.commit()

# IMPORTANT: Keep the static audit route above the generic
# /api/admin/{resource} route. Otherwise "/api/admin/audit" is interpreted
# as resource="audit" and the generic handler returns 404.
@app.get("/api/admin/audit")
def audit_logs(limit:int=Query(100,le=500), db:Session=Depends(get_db), user:User=Depends(current_user)):
    rows=db.scalars(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit)).all(); return [{c.name:getattr(r,c.name) for c in r.__table__.columns} for r in rows]

# IMPORTANT: Static admin routes must be declared above the generic
# /api/admin/{resource} routes. Otherwise paths such as /api/admin/payments
# are captured as resource="payments" and return 404.
@app.get("/api/admin/payments")
def payments(db:Session=Depends(get_db), user:User=Depends(current_user)):
    rows=db.scalars(select(Payment).order_by(desc(Payment.created_at))).all(); return [{c.name:getattr(r,c.name) for c in r.__table__.columns} for r in rows]

@app.post("/api/admin/payments", status_code=201)
def create_payment(data:PaymentCreate, db:Session=Depends(get_db), user:User=Depends(current_user)):
    p=Payment(reference=make_reference("PAY"),**data.model_dump()); db.add(p); db.flush(); audit(db,user,"Created payment record","payment",p.id,{"reference":p.reference}); db.commit(); return {c.name:getattr(p,c.name) for c in p.__table__.columns}

@app.patch("/api/admin/payments/{payment_id}")
def update_payment(payment_id:int,data:PaymentUpdate,db:Session=Depends(get_db),user:User=Depends(current_user)):
    p=db.get(Payment,payment_id)
    if not p: raise HTTPException(404,"Payment not found")
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(p,k,v)
    audit(db,user,"Updated payment","payment",p.id,{"status":p.status}); db.commit(); return {c.name:getattr(p,c.name) for c in p.__table__.columns}

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
if FRONTEND.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND / "assets"), name="assets")
    app.mount("/admin/static", StaticFiles(directory=FRONTEND / "admin"), name="admin-static")
    @app.get("/")
    def home(): return FileResponse(FRONTEND / "index.html")
    @app.get("/styles.css")
    def styles(): return FileResponse(FRONTEND / "styles.css", media_type="text/css")
    @app.get("/script.js")
    def script(): return FileResponse(FRONTEND / "script.js", media_type="application/javascript")
    @app.get("/admin")
    @app.get("/admin/")
    def admin_page(): return FileResponse(FRONTEND / "admin" / "index.html")
    @app.get("/admin/admin.css")
    def admin_css(): return FileResponse(FRONTEND / "admin" / "admin.css", media_type="text/css")
    @app.get("/funding-integration-v2.css")
    def funding_integration_v2_css(): return FileResponse(FRONTEND / "funding-integration-v2.css", media_type="text/css")
    @app.get("/funding-integration-v2.js")
    def funding_integration_v2_js(): return FileResponse(FRONTEND / "funding-integration-v2.js", media_type="application/javascript")
    @app.get("/admin/funding-integration-v2.css")
    def admin_funding_integration_v2_css(): return FileResponse(FRONTEND / "admin" / "funding-integration-v2.css", media_type="text/css")
    @app.get("/admin/funding-integration-v2.js")
    def admin_funding_integration_v2_js(): return FileResponse(FRONTEND / "admin" / "funding-integration-v2.js", media_type="application/javascript")
    @app.get("/phase3-workspace.css")
    def phase3_workspace_css(): return FileResponse(FRONTEND / "phase3-workspace.css", media_type="text/css")
    @app.get("/phase3-workspace.js")
    def phase3_workspace_js(): return FileResponse(FRONTEND / "phase3-workspace.js", media_type="application/javascript")
    @app.get("/admin/phase3-workspace.css")
    def admin_phase3_workspace_css(): return FileResponse(FRONTEND / "admin" / "phase3-workspace.css", media_type="text/css")
    @app.get("/admin/phase3-workspace.js")
    def admin_phase3_workspace_js(): return FileResponse(FRONTEND / "admin" / "phase3-workspace.js", media_type="application/javascript")
    @app.get("/phase4-marketplace.css")
    def phase4_marketplace_css(): return FileResponse(FRONTEND / "phase4-marketplace.css", media_type="text/css")
    @app.get("/phase4-marketplace.js")
    def phase4_marketplace_js(): return FileResponse(FRONTEND / "phase4-marketplace.js", media_type="application/javascript")
    @app.get("/admin/phase4-marketplace.css")
    def admin_phase4_marketplace_css(): return FileResponse(FRONTEND / "admin" / "phase4-marketplace.css", media_type="text/css")
    @app.get("/admin/phase4-marketplace.js")
    def admin_phase4_marketplace_js(): return FileResponse(FRONTEND / "admin" / "phase4-marketplace.js", media_type="application/javascript")
    @app.get("/admin/admin.js")
    def admin_js(): return FileResponse(FRONTEND / "admin" / "admin.js", media_type="application/javascript")


@app.get("/api/admin/payments/{payment_id}")
def payment_detail(payment_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    p=db.get(Payment,payment_id)
    if not p: raise HTTPException(404,"Payment not found")
    result={c.name:getattr(p,c.name) for c in p.__table__.columns}
    result["receipt_url"]=(
        f"/api/payments/receipt/{p.external_reference}"
        if p.status=="Paid" and p.external_reference and p.external_reference.startswith("PSTK-")
        else None
    )
    return result

@app.get("/api/admin/executive-summary")
def executive_summary(db:Session=Depends(get_db), user:User=Depends(current_user)):
    provinces=[
        "Eastern Cape","Free State","Gauteng","KwaZulu-Natal","Limpopo",
        "Mpumalanga","North West","Northern Cape","Western Cape"
    ]
    aliases={
        "EC":"Eastern Cape","FS":"Free State","GP":"Gauteng","KZN":"KwaZulu-Natal",
        "LP":"Limpopo","MP":"Mpumalanga","NW":"North West","NC":"Northern Cape","WC":"Western Cape"
    }
    def province_of(value):
        raw=(value or "").strip()
        upper=raw.upper().replace("."," ")
        for code,name in aliases.items():
            if upper==code or f" {code} " in f" {upper} ": return name
        for name in provinces:
            if name.upper() in upper: return name
        return "Not specified"

    farmers=db.scalars(select(Farmer)).all()
    buyers=db.scalars(select(Buyer)).all()
    orders=db.scalars(select(Order)).all()
    payments=db.scalars(select(Payment).where(Payment.status=="Paid")).all()
    memberships=db.scalars(select(MembershipApplication)).all()

    result=[]
    for province in provinces:
        pf=[x for x in farmers if province_of(x.location)==province]
        pb=[x for x in buyers if province_of(x.location)==province]
        po=[x for x in orders if province_of(x.delivery_area)==province]
        entity_ids={x.id for x in po}
        revenue=sum(
            float(x.amount or 0) for x in payments
            if x.entity_type=="order" and x.entity_id in entity_ids
        )
        result.append({
            "province":province,
            "farmers":len(pf),
            "approved_farmers":sum(1 for x in pf if x.status=="Approved"),
            "buyers":len(pb),
            "approved_buyers":sum(1 for x in pb if x.status=="Approved"),
            "orders":len(po),
            "revenue":round(revenue,2),
        })

    paid_total=sum(float(x.amount or 0) for x in payments)
    return {
        "provinces":result,
        "national":{
            "farmers":len(farmers),
            "buyers":len(buyers),
            "orders":len(orders),
            "memberships":len(memberships),
            "paid_revenue":round(paid_total,2),
            "pending_approvals":sum(1 for x in farmers+buyers+memberships if x.status=="Pending"),
        }
    }


# FARMLINK_PUBLIC_MARKETPLACE_V1
@app.get("/api/marketplace/suppliers")
def public_marketplace_suppliers(
    location: str | None = Query(None, max_length=120),
    product: str | None = Query(None, max_length=120),
    limit: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
):
    """
    Privacy-safe public supplier discovery endpoint.
    Only approved suppliers are returned. Private contact details and internal
    notes are never exposed.
    """
    query = select(Farmer).where(Farmer.status == "Approved")

    if location:
        term = f"%{location.strip()}%"
        query = query.where(Farmer.location.ilike(term))

    if product:
        term = f"%{product.strip()}%"
        query = query.where(
            or_(
                Farmer.producer_type.ilike(term),
                Farmer.egg_sizes.ilike(term),
                Farmer.packaging.ilike(term),
                Farmer.notes.ilike(term),
            )
        )

    farmers = db.scalars(
        query.order_by(desc(Farmer.updated_at), desc(Farmer.created_at)).limit(limit)
    ).all()

    results = []
    for farmer in farmers:
        available_trays = db.scalar(
            select(func.coalesce(func.sum(InventoryLot.trays_available), 0)).where(
                InventoryLot.farmer_id == farmer.id,
                InventoryLot.status == "Available",
            )
        ) or 0

        results.append({
            "id": farmer.id,
            "reference": farmer.reference,
            "farm_name": farmer.farm_name,
            "location": farmer.location,
            "producer_type": farmer.producer_type,
            "weekly_capacity": farmer.weekly_capacity,
            "egg_sizes": farmer.egg_sizes,
            "packaging": farmer.packaging,
            "delivery_capability": farmer.delivery_capability,
            "available_trays": int(available_trays),
            "updated_at": farmer.updated_at,
        })

    return {
        "items": results,
        "count": len(results),
        "filters": {"location": location, "product": product},
        "privacy": "Only approved public business information is displayed.",
    }

@app.get("/api/marketplace/summary")
def public_marketplace_summary(db: Session = Depends(get_db)):
    approved_farmers = db.scalar(
        select(func.count()).select_from(Farmer).where(Farmer.status == "Approved")
    ) or 0
    approved_buyers = db.scalar(
        select(func.count()).select_from(Buyer).where(Buyer.status == "Approved")
    ) or 0
    available_trays = db.scalar(
        select(func.coalesce(func.sum(InventoryLot.trays_available), 0)).where(
            InventoryLot.status == "Available"
        )
    ) or 0
    return {
        "approved_farmers": approved_farmers,
        "approved_buyers": approved_buyers,
        "available_trays": int(available_trays),
    }

# FARMLINK_MARKETPLACE_BACKEND_V1
@app.get("/api/marketplace/suppliers/{reference}")
def public_supplier_profile(reference: str, db: Session = Depends(get_db)):
    farmer = db.scalar(
        select(Farmer).where(
            Farmer.reference == reference,
            Farmer.status == "Approved",
        )
    )
    if not farmer:
        raise HTTPException(404, "Approved supplier profile not found")

    lots = db.scalars(
        select(InventoryLot).where(
            InventoryLot.farmer_id == farmer.id,
            InventoryLot.status == "Available",
        ).order_by(desc(InventoryLot.updated_at)).limit(30)
    ).all()

    return {
        "supplier": {
            "reference": farmer.reference,
            "farm_name": farmer.farm_name,
            "location": farmer.location,
            "producer_type": farmer.producer_type,
            "weekly_capacity": farmer.weekly_capacity,
            "egg_sizes": farmer.egg_sizes,
            "packaging": farmer.packaging,
            "delivery_capability": farmer.delivery_capability,
            "updated_at": farmer.updated_at,
        },
        "inventory": [
            {
                "reference": lot.reference,
                "egg_size": lot.egg_size,
                "packaging": lot.packaging,
                "trays_available": lot.trays_available,
                "unit_price": float(lot.unit_price) if lot.unit_price is not None else None,
                "available_from": lot.available_from,
                "expiry_date": lot.expiry_date,
                "updated_at": lot.updated_at,
            }
            for lot in lots
        ],
        "privacy": "Private supplier contact information is not published.",
    }


@app.get("/api/marketplace/inventory")
def public_inventory(
    location: str | None = Query(None, max_length=120),
    egg_size: str | None = Query(None, max_length=80),
    limit: int = Query(24, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = (
        select(InventoryLot, Farmer)
        .join(Farmer, Farmer.id == InventoryLot.farmer_id)
        .where(
            InventoryLot.status == "Available",
            InventoryLot.trays_available > 0,
            Farmer.status == "Approved",
        )
    )

    if location:
        query = query.where(Farmer.location.ilike(f"%{location.strip()}%"))

    if egg_size:
        query = query.where(InventoryLot.egg_size.ilike(f"%{egg_size.strip()}%"))

    rows = db.execute(
        query.order_by(desc(InventoryLot.updated_at)).limit(limit)
    ).all()

    return {
        "items": [
            {
                "inventory_reference": lot.reference,
                "supplier_reference": farmer.reference,
                "farm_name": farmer.farm_name,
                "location": farmer.location,
                "egg_size": lot.egg_size,
                "packaging": lot.packaging,
                "trays_available": lot.trays_available,
                "unit_price": float(lot.unit_price) if lot.unit_price is not None else None,
                "available_from": lot.available_from,
                "updated_at": lot.updated_at,
            }
            for lot, farmer in rows
        ]
    }


@app.post("/api/marketplace/quote-requests", status_code=201)
async def public_quote_request(request: Request, db: Session = Depends(get_db)):
    data = await request.json()

    required_fields = [
        "business_name",
        "contact_person",
        "phone",
        "email",
        "customer_type",
        "delivery_area",
        "product",
        "packaging",
        "quantity",
        "frequency",
        "required_date",
    ]

    missing = [
        field
        for field in required_fields
        if not str(data.get(field, "")).strip()
    ]

    if missing:
        raise HTTPException(
            422,
            f"Missing required fields: {', '.join(missing)}",
        )

    try:
        required_date = datetime.strptime(
            str(data["required_date"]),
            "%Y-%m-%d",
        ).date()
    except ValueError:
        raise HTTPException(
            422,
            "required_date must use YYYY-MM-DD",
        )

    supplier_reference = str(data.get("supplier_reference", "")).strip() or None
    inventory_reference = str(data.get("inventory_reference", "")).strip() or None

    if supplier_reference:
        supplier = db.scalar(
            select(Farmer).where(
                Farmer.reference == supplier_reference,
                Farmer.status == "Approved",
            )
        )
        if not supplier:
            raise HTTPException(404, "Selected supplier is unavailable")

    notes = str(data.get("notes", "")).strip()
    source_notes = [
        "Submitted through public marketplace quotation workflow.",
        f"Product requested: {str(data['product']).strip()}",
    ]
    if supplier_reference:
        source_notes.append(f"Preferred supplier: {supplier_reference}")
    if inventory_reference:
        source_notes.append(f"Inventory reference: {inventory_reference}")
    if notes:
        source_notes.append(f"Buyer notes: {notes}")

    order = Order(
        reference=make_reference("ORD"),
        business_name=str(data["business_name"]).strip(),
        contact_person=str(data["contact_person"]).strip(),
        phone=str(data["phone"]).strip(),
        email=str(data["email"]).strip().lower(),
        customer_type=str(data["customer_type"]).strip(),
        delivery_area=str(data["delivery_area"]).strip(),
        egg_size=str(data["product"]).strip(),
        packaging=str(data["packaging"]).strip(),
        quantity=str(data["quantity"]).strip(),
        frequency=str(data["frequency"]).strip(),
        required_date=required_date,
        notes="\n".join(source_notes),
        status="Pending",
    )

    db.add(order)
    db.flush()

    audit(
        db,
        None,
        "Submitted marketplace quotation request",
        "order",
        order.id,
        {
            "reference": order.reference,
            "supplier_reference": supplier_reference,
            "inventory_reference": inventory_reference,
        },
        request.client.host if request.client else None,
    )

    db.commit()
    db.refresh(order)

    return {
        "reference": order.reference,
        "status": order.status,
        "message": "Your quotation request has been submitted for commercial review.",
    }



# FARMLINK_MARKETPLACE_ADMIN_V9
@app.get("/api/admin/marketplace/overview")
def marketplace_admin_overview(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    approved_suppliers = db.scalar(
        select(func.count()).select_from(Farmer).where(Farmer.status == "Approved")
    ) or 0
    active_inventory_lots = db.scalar(
        select(func.count()).select_from(InventoryLot).where(
            InventoryLot.status == "Available"
        )
    ) or 0
    available_trays = db.scalar(
        select(func.coalesce(func.sum(InventoryLot.trays_available), 0)).where(
            InventoryLot.status == "Available"
        )
    ) or 0
    marketplace_quotes = db.scalar(
        select(func.count()).select_from(Order).where(
            Order.notes.ilike("%public marketplace quotation workflow%")
        )
    ) or 0
    pending_quotes = db.scalar(
        select(func.count()).select_from(Order).where(
            Order.notes.ilike("%public marketplace quotation workflow%"),
            Order.status.in_(["Pending", "In progress"]),
        )
    ) or 0
    quoted_value = db.scalar(
        select(func.coalesce(func.sum(Order.quoted_amount), 0)).where(
            Order.notes.ilike("%public marketplace quotation workflow%"),
            Order.quoted_amount.is_not(None),
        )
    ) or 0

    return {
        "approved_suppliers": approved_suppliers,
        "active_inventory_lots": active_inventory_lots,
        "available_trays": int(available_trays),
        "marketplace_quotes": marketplace_quotes,
        "pending_quotes": pending_quotes,
        "quoted_value": float(quoted_value),
    }


@app.get("/api/admin/marketplace/inventory")
def marketplace_admin_inventory(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    rows = db.execute(
        select(InventoryLot, Farmer)
        .join(Farmer, Farmer.id == InventoryLot.farmer_id)
        .order_by(desc(InventoryLot.updated_at))
    ).all()

    return [
        {
            "id": lot.id,
            "reference": lot.reference,
            "farmer_id": lot.farmer_id,
            "farmer_name": farmer.farm_name,
            "location": farmer.location,
            "farmer_status": farmer.status,
            "egg_size": lot.egg_size,
            "packaging": lot.packaging,
            "trays_available": lot.trays_available,
            "unit_price": float(lot.unit_price) if lot.unit_price is not None else None,
            "available_from": lot.available_from,
            "expiry_date": lot.expiry_date,
            "status": lot.status,
            "notes": lot.notes,
            "created_at": lot.created_at,
            "updated_at": lot.updated_at,
        }
        for lot, farmer in rows
    ]


@app.post("/api/admin/marketplace/inventory", status_code=201)
async def marketplace_admin_create_inventory(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    data = await request.json()
    required = ["farmer_id", "egg_size", "packaging", "trays_available", "status"]
    missing = [field for field in required if data.get(field) in (None, "")]
    if missing:
        raise HTTPException(422, f"Missing required fields: {', '.join(missing)}")

    farmer = db.get(Farmer, int(data["farmer_id"]))
    if not farmer:
        raise HTTPException(404, "Farmer not found")
    if farmer.status != "Approved":
        raise HTTPException(400, "Only approved farmers can receive public inventory")

    lot = InventoryLot(
        reference=make_reference("INV"),
        farmer_id=farmer.id,
        egg_size=str(data["egg_size"]).strip(),
        packaging=str(data["packaging"]).strip(),
        trays_available=max(0, int(data["trays_available"])),
        unit_price=(
            float(data["unit_price"])
            if data.get("unit_price") not in (None, "")
            else None
        ),
        available_from=(
            datetime.strptime(str(data["available_from"]), "%Y-%m-%d").date()
            if data.get("available_from")
            else datetime.utcnow().date()
        ),
        expiry_date=(
            datetime.strptime(str(data["expiry_date"]), "%Y-%m-%d").date()
            if data.get("expiry_date")
            else None
        ),
        status=str(data["status"]).strip(),
        notes=str(data.get("notes", "")).strip() or None,
    )
    db.add(lot)
    db.flush()
    audit(
        db,
        user,
        "Created marketplace inventory",
        "inventory",
        lot.id,
        {
            "reference": lot.reference,
            "farmer_reference": farmer.reference,
            "trays_available": lot.trays_available,
            "status": lot.status,
        },
        request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(lot)
    return {"id": lot.id, "reference": lot.reference, "status": lot.status}


@app.patch("/api/admin/marketplace/inventory/{inventory_id}")
async def marketplace_admin_update_inventory(
    inventory_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    lot = db.get(InventoryLot, inventory_id)
    if not lot:
        raise HTTPException(404, "Inventory lot not found")

    data = await request.json()
    before = {
        "egg_size": lot.egg_size,
        "packaging": lot.packaging,
        "trays_available": lot.trays_available,
        "unit_price": float(lot.unit_price) if lot.unit_price is not None else None,
        "status": lot.status,
    }

    for field in ["egg_size", "packaging", "status", "notes"]:
        if field in data:
            value = str(data[field]).strip()
            setattr(lot, field, value or None if field == "notes" else value)

    if "trays_available" in data:
        lot.trays_available = max(0, int(data["trays_available"]))
    if "unit_price" in data:
        lot.unit_price = (
            float(data["unit_price"])
            if data["unit_price"] not in (None, "")
            else None
        )
    if "available_from" in data and data["available_from"]:
        lot.available_from = datetime.strptime(
            str(data["available_from"]), "%Y-%m-%d"
        ).date()
    if "expiry_date" in data:
        lot.expiry_date = (
            datetime.strptime(str(data["expiry_date"]), "%Y-%m-%d").date()
            if data["expiry_date"]
            else None
        )

    after = {
        "egg_size": lot.egg_size,
        "packaging": lot.packaging,
        "trays_available": lot.trays_available,
        "unit_price": float(lot.unit_price) if lot.unit_price is not None else None,
        "status": lot.status,
    }
    audit(
        db,
        user,
        "Updated marketplace inventory",
        "inventory",
        lot.id,
        {"reference": lot.reference, "before": before, "after": after},
        request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(lot)
    return {
        "id": lot.id,
        "reference": lot.reference,
        "status": lot.status,
        "trays_available": lot.trays_available,
    }


@app.delete("/api/admin/marketplace/inventory/{inventory_id}", status_code=204)
def marketplace_admin_delete_inventory(
    inventory_id: int,
    request: Request,
    db: Session = Depends(get_db),
    ceo: User = Depends(ceo_user),
):
    lot = db.get(InventoryLot, inventory_id)
    if not lot:
        raise HTTPException(404, "Inventory lot not found")
    audit(
        db,
        ceo,
        "Removed marketplace inventory",
        "inventory",
        lot.id,
        {"reference": lot.reference},
        request.client.host if request.client else None,
    )
    db.delete(lot)
    db.commit()


@app.get("/api/admin/marketplace/quotes")
def marketplace_admin_quotes(
    status: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    query = select(Order).where(
        Order.notes.ilike("%public marketplace quotation workflow%")
    )
    if status and status != "all":
        query = query.where(Order.status == status)
    rows = db.scalars(query.order_by(desc(Order.created_at))).all()
    return [serialize(row) for row in rows]


@app.patch("/api/admin/marketplace/quotes/{order_id}")
async def marketplace_admin_update_quote(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(404, "Quotation request not found")
    if "public marketplace quotation workflow" not in (order.notes or "").lower():
        raise HTTPException(400, "This order is not a marketplace quotation request")

    data = await request.json()
    before = {
        "status": order.status,
        "quoted_amount": float(order.quoted_amount) if order.quoted_amount is not None else None,
        "assigned_to_id": order.assigned_to_id,
    }

    if "status" in data:
        order.status = str(data["status"]).strip()
    if "quoted_amount" in data:
        order.quoted_amount = (
            float(data["quoted_amount"])
            if data["quoted_amount"] not in (None, "")
            else None
        )
    if "assigned_to_id" in data:
        assigned_to_id = data["assigned_to_id"]
        if assigned_to_id in (None, ""):
            order.assigned_to_id = None
        else:
            assignee = db.get(User, int(assigned_to_id))
            if not assignee or not assignee.is_active:
                raise HTTPException(400, "Invalid administrator assignment")
            order.assigned_to_id = assignee.id
    if "internal_notes" in data:
        order.internal_notes = str(data["internal_notes"]).strip() or None

    after = {
        "status": order.status,
        "quoted_amount": float(order.quoted_amount) if order.quoted_amount is not None else None,
        "assigned_to_id": order.assigned_to_id,
    }
    audit(
        db,
        user,
        "Updated marketplace quotation",
        "order",
        order.id,
        {"reference": order.reference, "before": before, "after": after},
        request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(order)
    return serialize(order)



@app.get("/api/admin/{resource}")
def list_records(resource: str, q: str|None=None, status: str|None=None, limit:int=Query(100,le=500), offset:int=0, db:Session=Depends(get_db), user:User=Depends(current_user)):
    model=MODEL_MAP.get(resource)
    if not model: raise HTTPException(404,"Unknown resource")
    stmt=select(model)
    if status and status!="all": stmt=stmt.where(model.status==status)
    if q:
        fields=[]
        for name in ["reference","farm_name","business_name","contact_person","full_name","location","delivery_area","province","municipality","institution","qualification","agricultural_interest","email","phone"]:
            if hasattr(model,name): fields.append(getattr(model,name).ilike(f"%{q}%"))
        if fields: stmt=stmt.where(or_(*fields))
    total=db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows=db.scalars(stmt.order_by(desc(model.created_at)).offset(offset).limit(limit)).all()
    return {"total":total,"items":[serialize(x) for x in rows]}

@app.get("/api/admin/{resource}/{record_id}")
def get_record(resource:str, record_id:int, db:Session=Depends(get_db), user:User=Depends(current_user)):
    model=MODEL_MAP.get(resource); rec=db.get(model,record_id) if model else None
    if not rec: raise HTTPException(404,"Record not found")
    return serialize(rec)

@app.patch("/api/admin/{resource}/{record_id}")
def update_record(resource:str, record_id:int, data:RecordUpdate, request:Request, db:Session=Depends(get_db), user:User=Depends(current_user)):
    model=MODEL_MAP.get(resource); rec=db.get(model,record_id) if model else None
    if not rec: raise HTTPException(404,"Record not found")
    changes={}
    for k,v in data.model_dump(exclude_unset=True).items():
        if k=="quoted_amount" and not hasattr(rec,k): continue
        if k=="assigned_to_id" and v is not None:
            assignee=db.get(User,v)
            if not assignee or not assignee.is_active: raise HTTPException(400,"Invalid assignee")
        old=getattr(rec,k,None); setattr(rec,k,v); changes[k]={"from":str(old),"to":str(v)}
    audit(db,user,"Updated record",resource[:-1],rec.id,{"reference":rec.reference,"changes":changes},request.client.host if request.client else None); db.commit(); db.refresh(rec); return serialize(rec)


