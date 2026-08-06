from __future__ import annotations

from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from .database import get_db
from .deps import current_user
from .models import EntrepreneurshipApplication, StoredDocument, User
from .phase3_models import (
    DocumentReview,
    EntrepreneurTask,
    EntrepreneurWorkspace,
    MentorSession,
)
from .phase3_schemas import (
    BUSINESS_STAGES,
    DOCUMENT_REVIEW_STATUSES,
    DOCUMENT_TYPES,
    MentorSessionCreate,
    MentorSessionUpdate,
    PublicWorkspaceAccess,
    TaskCreate,
    TaskUpdate,
    WorkspaceUpdate,
)
from .utils import audit, make_reference


router = APIRouter(prefix="/api", tags=["AgriStart Phase 3"])

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
MAX_FILE_SIZE = 10 * 1024 * 1024


def serialize(record) -> dict:
    return {
        column.name: getattr(record, column.name)
        for column in record.__table__.columns
        if column.name != "file_data"
    }


def get_entrepreneur(db: Session, entrepreneur_id: int) -> EntrepreneurshipApplication:
    record = db.get(EntrepreneurshipApplication, entrepreneur_id)
    if not record:
        raise HTTPException(404, "AgriStart applicant not found")
    return record


def get_or_create_workspace(
    db: Session,
    entrepreneur_id: int,
) -> EntrepreneurWorkspace:
    workspace = db.scalar(
        select(EntrepreneurWorkspace).where(
            EntrepreneurWorkspace.entrepreneur_id == entrepreneur_id
        )
    )
    if workspace:
        return workspace

    applicant = get_entrepreneur(db, entrepreneur_id)
    workspace = EntrepreneurWorkspace(
        entrepreneur_id=entrepreneur_id,
        business_name=None,
        next_action="Complete business profile and upload required documents",
        funding_status="Not started",
        launch_status="Not started",
    )
    db.add(workspace)
    db.flush()
    return workspace


def document_rows(db: Session, entrepreneur_id: int) -> list[dict]:
    documents = db.scalars(
        select(StoredDocument)
        .where(
            StoredDocument.entity_type == "entrepreneur",
            StoredDocument.entity_id == entrepreneur_id,
        )
        .order_by(desc(StoredDocument.created_at))
    ).all()

    reviews = {
        review.document_id: review
        for review in db.scalars(
            select(DocumentReview).where(
                DocumentReview.document_id.in_([doc.id for doc in documents])
            )
        ).all()
    } if documents else {}

    rows = []
    for document in documents:
        item = serialize(document)
        review = reviews.get(document.id)
        item["review_status"] = (
            review.review_status if review else "Pending review"
        )
        item["reviewer_comment"] = review.reviewer_comment if review else None
        item["reviewed_at"] = review.reviewed_at if review else None
        item["download_url"] = f"/api/admin/documents/{document.id}/download"
        rows.append(item)
    return rows


def readiness_breakdown(db: Session, entrepreneur_id: int) -> dict:
    workspace = get_or_create_workspace(db, entrepreneur_id)
    documents = document_rows(db, entrepreneur_id)
    approved_types = {
        item["document_type"]
        for item in documents
        if item["review_status"] == "Approved"
    }

    required_types = {
        "CIPC Registration",
        "Tax Compliance",
        "Bank Confirmation Letter",
        "Business Plan",
        "Cash-flow Projection",
        "Pitch Deck",
    }
    document_score = round(
        len(required_types & approved_types) / len(required_types) * 45
    )

    business_score = 0
    business_score += 10 if workspace.business_name else 0
    business_score += 10 if workspace.business_stage not in {"Idea stage", "Validation"} else 0
    business_score += 5 if workspace.next_action else 0

    mentorship_score = 10 if workspace.assigned_mentor_id else 0
    funding_score = 10 if workspace.funding_status in {"Funding ready", "Approved"} else 0
    launch_score = 10 if workspace.launch_status in {"Launch ready", "Launched"} else 0

    total = min(
        100,
        document_score
        + business_score
        + mentorship_score
        + funding_score
        + launch_score,
    )
    return {
        "overall": total,
        "documents": document_score,
        "business": business_score,
        "mentorship": mentorship_score,
        "funding": funding_score,
        "launch": launch_score,
        "approved_document_types": sorted(approved_types),
        "required_document_types": sorted(required_types),
    }


def workspace_payload(db: Session, entrepreneur_id: int) -> dict:
    applicant = get_entrepreneur(db, entrepreneur_id)
    workspace = get_or_create_workspace(db, entrepreneur_id)
    tasks = db.scalars(
        select(EntrepreneurTask)
        .where(EntrepreneurTask.entrepreneur_id == entrepreneur_id)
        .order_by(EntrepreneurTask.due_date, desc(EntrepreneurTask.created_at))
    ).all()
    sessions = db.scalars(
        select(MentorSession)
        .where(MentorSession.entrepreneur_id == entrepreneur_id)
        .order_by(desc(MentorSession.session_date))
    ).all()

    return {
        "applicant": serialize(applicant),
        "workspace": serialize(workspace),
        "readiness": readiness_breakdown(db, entrepreneur_id),
        "documents": document_rows(db, entrepreneur_id),
        "tasks": [serialize(task) for task in tasks],
        "mentor_sessions": [serialize(session) for session in sessions],
    }


@router.get("/admin/phase3/dashboard")
def phase3_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    applicants = db.scalars(select(EntrepreneurshipApplication)).all()
    workspaces = {
        item.entrepreneur_id: item
        for item in db.scalars(select(EntrepreneurWorkspace)).all()
    }

    scores = []
    rows = []
    for applicant in applicants:
        workspace = workspaces.get(applicant.id) or get_or_create_workspace(
            db, applicant.id
        )
        score = readiness_breakdown(db, applicant.id)["overall"]
        scores.append(score)
        rows.append(
            {
                "id": applicant.id,
                "reference": applicant.reference,
                "full_name": applicant.full_name,
                "email": applicant.email,
                "province": applicant.province,
                "agricultural_interest": applicant.agricultural_interest,
                "business_name": workspace.business_name,
                "business_stage": workspace.business_stage,
                "funding_status": workspace.funding_status,
                "launch_status": workspace.launch_status,
                "marketplace_status": workspace.marketplace_status,
                "supplier_verification_status": workspace.supplier_verification_status,
                "next_action": workspace.next_action,
                "readiness_score": score,
            }
        )

    db.commit()
    return {
        "summary": {
            "total": len(rows),
            "average_readiness": round(sum(scores) / len(scores)) if scores else 0,
            "funding_ready": sum(
                1 for row in rows if row["funding_status"] == "Funding ready"
            ),
            "launch_ready": sum(
                1 for row in rows if row["launch_status"] == "Launch ready"
            ),
            "launched": sum(
                1 for row in rows if row["launch_status"] == "Launched"
            ),
            "verified_suppliers": sum(
                1
                for row in rows
                if row["supplier_verification_status"] == "Verified"
            ),
        },
        "items": rows,
    }


@router.get("/admin/phase3/entrepreneurs/{entrepreneur_id}")
def admin_workspace_detail(
    entrepreneur_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    payload = workspace_payload(db, entrepreneur_id)
    db.commit()
    return payload


@router.patch("/admin/phase3/entrepreneurs/{entrepreneur_id}/workspace")
def update_workspace(
    entrepreneur_id: int,
    data: WorkspaceUpdate,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    workspace = get_or_create_workspace(db, entrepreneur_id)
    changes = {}
    for field, value in data.model_dump(exclude_unset=True).items():
        old = getattr(workspace, field)
        setattr(workspace, field, value)
        changes[field] = {"from": str(old), "to": str(value)}

    audit(
        db,
        user,
        "Updated Phase 3 business workspace",
        "entrepreneur",
        entrepreneur_id,
        changes,
        request.client.host if request.client else None,
    )
    db.commit()
    db.refresh(workspace)
    return {
        "workspace": serialize(workspace),
        "readiness": readiness_breakdown(db, entrepreneur_id),
    }


@router.post("/admin/phase3/entrepreneurs/{entrepreneur_id}/tasks", status_code=201)
def create_task(
    entrepreneur_id: int,
    data: TaskCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    get_entrepreneur(db, entrepreneur_id)
    task = EntrepreneurTask(
        entrepreneur_id=entrepreneur_id,
        **data.model_dump(),
    )
    db.add(task)
    db.flush()
    audit(db, user, "Created entrepreneur task", "entrepreneur_task", task.id)
    db.commit()
    db.refresh(task)
    return serialize(task)


@router.patch("/admin/phase3/tasks/{task_id}")
def update_task(
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    task = db.get(EntrepreneurTask, task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    if task.status == "Completed" and not task.completed_at:
        task.completed_at = datetime.utcnow()

    audit(db, user, "Updated entrepreneur task", "entrepreneur_task", task.id)
    db.commit()
    db.refresh(task)
    return serialize(task)


@router.post(
    "/admin/phase3/entrepreneurs/{entrepreneur_id}/mentor-sessions",
    status_code=201,
)
def create_mentor_session(
    entrepreneur_id: int,
    data: MentorSessionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    get_entrepreneur(db, entrepreneur_id)
    session = MentorSession(
        entrepreneur_id=entrepreneur_id,
        **data.model_dump(),
    )
    db.add(session)
    db.flush()
    audit(db, user, "Created mentor session", "mentor_session", session.id)
    db.commit()
    db.refresh(session)
    return serialize(session)


@router.patch("/admin/phase3/mentor-sessions/{session_id}")
def update_mentor_session(
    session_id: int,
    data: MentorSessionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    session = db.get(MentorSession, session_id)
    if not session:
        raise HTTPException(404, "Mentor session not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(session, field, value)
    audit(db, user, "Updated mentor session", "mentor_session", session.id)
    db.commit()
    db.refresh(session)
    return serialize(session)


@router.post(
    "/admin/phase3/entrepreneurs/{entrepreneur_id}/documents",
    status_code=201,
)
async def upload_phase3_document(
    entrepreneur_id: int,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    get_entrepreneur(db, entrepreneur_id)
    if document_type not in DOCUMENT_TYPES:
        raise HTTPException(400, "Unsupported document type")
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(415, "Unsupported file format")

    content = await file.read()
    if not content:
        raise HTTPException(400, "The uploaded file is empty")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "File exceeds 10 MB")

    document = StoredDocument(
        reference=make_reference("DOC"),
        entity_type="entrepreneur",
        entity_id=entrepreneur_id,
        document_type=document_type,
        filename=file.filename or "document",
        content_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        file_data=content,
        uploaded_by_id=user.id,
    )
    db.add(document)
    db.flush()
    review = DocumentReview(document_id=document.id)
    db.add(review)
    audit(db, user, "Uploaded Phase 3 document", "document", document.id)
    db.commit()
    return {
        **serialize(document),
        "review_status": review.review_status,
        "download_url": f"/api/admin/documents/{document.id}/download",
    }


@router.patch("/admin/phase3/documents/{document_id}/review")
def review_document(
    document_id: int,
    review_status: str,
    reviewer_comment: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    if review_status not in DOCUMENT_REVIEW_STATUSES:
        raise HTTPException(400, "Invalid document review status")

    document = db.get(StoredDocument, document_id)
    if not document or document.entity_type != "entrepreneur":
        raise HTTPException(404, "Entrepreneur document not found")

    review = db.scalar(
        select(DocumentReview).where(DocumentReview.document_id == document_id)
    )
    if not review:
        review = DocumentReview(document_id=document_id)
        db.add(review)

    review.review_status = review_status
    review.reviewer_comment = reviewer_comment
    review.reviewed_by_id = user.id
    review.reviewed_at = datetime.utcnow()
    audit(db, user, "Reviewed Phase 3 document", "document", document_id)
    db.commit()
    return {
        "document_id": document_id,
        "review_status": review.review_status,
        "reviewer_comment": review.reviewer_comment,
        "reviewed_at": review.reviewed_at,
    }


@router.post("/public/phase3/workspace")
def public_workspace(
    data: PublicWorkspaceAccess,
    db: Session = Depends(get_db),
):
    applicant = db.scalar(
        select(EntrepreneurshipApplication).where(
            EntrepreneurshipApplication.reference == data.reference.strip(),
            func.lower(EntrepreneurshipApplication.email)
            == data.email.strip().lower(),
        )
    )
    if not applicant:
        raise HTTPException(404, "No matching AgriStart workspace was found")

    payload = workspace_payload(db, applicant.id)
    db.commit()

    # Public response excludes internal notes, mentor notes and document downloads.
    payload["workspace"].pop("internal_notes", None)
    payload["applicant"].pop("internal_notes", None)
    payload["mentor_sessions"] = [
        {
            "session_date": item["session_date"],
            "session_type": item["session_type"],
            "status": item["status"],
            "objectives": item["objectives"],
        }
        for item in payload["mentor_sessions"]
    ]
    payload["documents"] = [
        {
            "document_type": item["document_type"],
            "filename": item["filename"],
            "review_status": item["review_status"],
            "reviewer_comment": item["reviewer_comment"],
            "created_at": item["created_at"],
        }
        for item in payload["documents"]
    ]
    return payload


@router.post("/public/phase3/documents", status_code=201)
async def public_document_upload(
    reference: str = Form(...),
    email: str = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    applicant = db.scalar(
        select(EntrepreneurshipApplication).where(
            EntrepreneurshipApplication.reference == reference.strip(),
            func.lower(EntrepreneurshipApplication.email) == email.strip().lower(),
        )
    )
    if not applicant:
        raise HTTPException(404, "No matching AgriStart workspace was found")
    if document_type not in DOCUMENT_TYPES:
        raise HTTPException(400, "Unsupported document type")
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(415, "Unsupported file format")

    content = await file.read()
    if not content:
        raise HTTPException(400, "The uploaded file is empty")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "File exceeds 10 MB")

    document = StoredDocument(
        reference=make_reference("DOC"),
        entity_type="entrepreneur",
        entity_id=applicant.id,
        document_type=document_type,
        filename=file.filename or "document",
        content_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        file_data=content,
        uploaded_by_id=None,
    )
    db.add(document)
    db.flush()
    db.add(DocumentReview(document_id=document.id))
    audit(
        db,
        None,
        "Uploaded public Phase 3 document",
        "document",
        document.id,
        {
            "entrepreneur_reference": applicant.reference,
            "document_type": document_type,
        },
        request.client.host if request and request.client else None,
    )
    db.commit()
    return {
        "reference": document.reference,
        "document_type": document.document_type,
        "review_status": "Pending review",
    }


@router.get("/public/phase3/options")
def phase3_options():
    return {
        "business_stages": BUSINESS_STAGES,
        "document_types": DOCUMENT_TYPES,
        "document_review_statuses": DOCUMENT_REVIEW_STATUSES,
    }
