from uuid import uuid4
from pathlib import Path
from fastapi import FastAPI, Depends, File, Form, HTTPException, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session
from .config import settings
from .database import Base, engine, get_db
from .models import Report, User
from .schemas import AssignIn, LoginIn, RegisterIn, ReportOut, StatusIn, TokenOut, UserOut
from .security import current_user, create_token, hash_password, require_roles, verify_password
from .services import ai_service, image_storage

Base.metadata.create_all(bind=engine)
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app = FastAPI(title="WasteWatch AI API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["GET","POST","PATCH","DELETE"], allow_headers=["Authorization","Content-Type"])
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

def report_out(r: Report, request: Request) -> ReportOut:
    return ReportOut(id=r.id, category=r.category, severity=r.severity, description=r.description, latitude=r.latitude, longitude=r.longitude, location_text=r.location_text, image_url=str(request.base_url).rstrip("/") + f"/uploads/{r.image_path}", status=r.status, predicted_category=r.predicted_category, confidence_score=r.confidence_score, ai_status=r.ai_status, requires_human_review=r.requires_human_review, supervisor_remarks=r.supervisor_remarks, assigned_to=r.assigned_to, created_at=r.created_at, owner_id=r.owner_id)

@app.get("/health")
def health(): return {"status":"ok", "service":"wastewatch-api", "ai":"not_configured"}

@app.post("/api/users/register", response_model=TokenOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)): raise HTTPException(409, "An account with this email already exists")
    user = User(name=data.name.strip(), email=email, password_hash=hash_password(data.password), role="citizen")
    db.add(user); db.commit(); db.refresh(user)
    return TokenOut(access_token=create_token(user), user=user)

@app.post("/api/users/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not verify_password(data.password, user.password_hash): raise HTTPException(401, "Email or password is incorrect")
    return TokenOut(access_token=create_token(user), user=user)

@app.get("/api/users/me", response_model=UserOut)
def me(user: User = Depends(current_user)): return user

@app.post("/api/reports", response_model=ReportOut, status_code=201)
async def create_report(request: Request, category: str = Form(...), severity: str = Form("Medium"), description: str = Form(...), latitude: float | None = Form(None), longitude: float | None = Form(None), location_text: str | None = Form(None), image: UploadFile = File(...), user: User = Depends(require_roles("citizen","admin")), db: Session = Depends(get_db)):
    categories = {"Mixed Waste","Plastic","Construction Debris","Organic","Hazardous","E-waste"}
    if category not in categories: raise HTTPException(422, "Unknown waste category")
    if severity not in {"Low","Medium","High","Critical"}: raise HTTPException(422, "Unknown urgency level")
    if len(description.strip()) < 5 or len(description) > 300: raise HTTPException(422, "Description must contain 5 to 300 characters")
    if (latitude is None) != (longitude is None): raise HTTPException(422, "Latitude and longitude must be provided together")
    if latitude is not None and not -90 <= latitude <= 90: raise HTTPException(422, "Latitude must be between -90 and 90")
    if longitude is not None and not -180 <= longitude <= 180: raise HTTPException(422, "Longitude must be between -180 and 180")
    filename = await image_storage.save(image)
    ai = ai_service.predict(filename)
    row = Report(id=f"WW-{uuid4().hex[:10].upper()}", owner_id=user.id, category=category, severity=severity, description=description.strip(), latitude=latitude, longitude=longitude, location_text=location_text, image_path=filename, status="review", **ai)
    db.add(row); db.commit(); db.refresh(row)
    return report_out(row, request)

@app.get("/api/reports", response_model=list[ReportOut])
def list_reports(request: Request, status: str | None = None, category: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)):
    query = select(Report).order_by(Report.created_at.desc())
    if user.role == "citizen": query = query.where(Report.owner_id == user.id)
    if user.role == "collector": query = query.where(Report.assigned_to == user.email)
    if status: query = query.where(Report.status == status)
    if category: query = query.where(Report.category == category)
    return [report_out(r, request) for r in db.scalars(query).all()]

@app.get("/api/reports/{report_id}", response_model=ReportOut)
def get_report(report_id: str, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.get(Report, report_id)
    if not row: raise HTTPException(404, "Report not found")
    if user.role == "citizen" and row.owner_id != user.id: raise HTTPException(403, "You can only view your own reports")
    if user.role == "collector" and row.assigned_to != user.email: raise HTTPException(403, "This cleanup task is not assigned to you")
    return report_out(row, request)

@app.patch("/api/reports/{report_id}/status", response_model=ReportOut)
def update_status(report_id: str, data: StatusIn, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.get(Report, report_id)
    if not row: raise HTTPException(404, "Report not found")
    if user.role in {"supervisor","admin"}:
        allowed = {"submitted":{"review","verified","rejected"},"review":{"verified","rejected"},"await":{"resolved","cleaning"}}
    elif user.role == "collector":
        if row.assigned_to != user.email: raise HTTPException(403, "This cleanup task is not assigned to you")
        allowed = {"assigned":{"accepted"},"accepted":{"way"},"way":{"arrived"},"arrived":{"cleaning"},"cleaning":{"await"}}
    else: raise HTTPException(403, "Your account cannot update report status")
    if data.status not in allowed.get(row.status, set()): raise HTTPException(409, f"Cannot change status from {row.status} to {data.status}")
    row.status = data.status
    if data.remarks is not None:
        if user.role not in {"supervisor","admin"}: raise HTTPException(403, "Only reviewers can add remarks")
        row.supervisor_remarks = data.remarks
    db.commit(); db.refresh(row)
    return report_out(row, request)

@app.patch("/api/reports/{report_id}/assign", response_model=ReportOut)
def assign_report(report_id: str, data: AssignIn, request: Request, user: User = Depends(require_roles("supervisor","admin")), db: Session = Depends(get_db)):
    row = db.get(Report, report_id)
    if not row: raise HTTPException(404, "Report not found")
    if row.status != "verified": raise HTTPException(409, "Only verified reports can be assigned")
    collector = db.scalar(select(User).where(User.email == data.collector_email.lower(), User.role == "collector"))
    if not collector: raise HTTPException(404, "No collector account found for that email")
    row.assigned_to = collector.email
    row.status = "assigned"
    db.commit(); db.refresh(row)
    return report_out(row, request)

@app.delete("/api/reports/{report_id}", status_code=204)
def delete_report(report_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    row = db.get(Report, report_id)
    if not row: raise HTTPException(404, "Report not found")
    if user.role != "admin" and not (user.role == "citizen" and row.owner_id == user.id and row.status in {"submitted","review"}): raise HTTPException(403, "You cannot delete this report")
    image_storage.delete(row.image_path); db.delete(row); db.commit()

