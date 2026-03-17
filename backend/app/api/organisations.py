from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import secrets
import string

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin
from app.models.user import User, Organisation, UserProgress, RiskAssessment, LearningModule

router = APIRouter()

def generate_invite_code():
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(8))

class OrgCreate(BaseModel):
    name: str
    sector: Optional[str] = None
    size: Optional[str] = "SME"

class JoinOrg(BaseModel):
    invite_code: str

@router.post("/create", status_code=201)
async def create_organisation(payload: OrgCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invite_code = generate_invite_code()
    while db.query(Organisation).filter(Organisation.invite_code == invite_code).first():
        invite_code = generate_invite_code()
    org = Organisation(name=payload.name, sector=payload.sector, size=payload.size, invite_code=invite_code)
    db.add(org)
    db.flush()
    current_user.organisation_id = org.id
    db.commit()
    return {"id": org.id, "name": org.name, "invite_code": invite_code}

@router.post("/join")
async def join_organisation(payload: JoinOrg, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    org = db.query(Organisation).filter(Organisation.invite_code == payload.invite_code.upper()).first()
    if not org:
        raise HTTPException(404, "Invalid invite code")
    current_user.organisation_id = org.id
    db.commit()
    return {"message": f"Joined {org.name}", "org_id": org.id}

@router.get("/my")
async def get_my_org(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.organisation_id:
        return None
    org = db.query(Organisation).filter(Organisation.id == current_user.organisation_id).first()
    if not org:
        return None
    members = db.query(User).filter(User.organisation_id == org.id, User.is_active == True).all()
    return {
        "id": org.id,
        "name": org.name,
        "sector": org.sector,
        "size": org.size,
        "invite_code": org.invite_code,
        "member_count": len(members),
    }

@router.get("/health")
async def get_org_health(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.organisation_id:
        raise HTTPException(404, "Not part of an organisation")

    org = db.query(Organisation).filter(Organisation.id == current_user.organisation_id).first()
    members = db.query(User).filter(User.organisation_id == org.id, User.is_active == True).all()
    member_ids = [m.id for m in members]

    total_modules = db.query(LearningModule).filter(LearningModule.is_published == True).count()

    member_stats = []
    total_completions = 0
    total_score = 0
    scored_assessments = 0

    for member in members:
        completions = db.query(UserProgress).filter(
            UserProgress.user_id == member.id,
            UserProgress.status == "completed"
        ).count()
        assessment = db.query(RiskAssessment).filter(
            RiskAssessment.user_id == member.id
        ).order_by(RiskAssessment.created_at.desc()).first()

        score = assessment.overall_score if assessment else None
        if score:
            total_score += score
            scored_assessments += 1

        total_completions += completions
        progress_pct = round((completions / total_modules) * 100) if total_modules > 0 else 0

        member_stats.append({
            "id": member.id,
            "name": member.full_name or member.email,
            "email": member.email,
            "modules_completed": completions,
            "progress_percent": progress_pct,
            "risk_score": score,
        })

    avg_score = round(total_score / scored_assessments) if scored_assessments > 0 else None
    avg_progress = round(sum(m["progress_percent"] for m in member_stats) / len(member_stats)) if member_stats else 0

    # Health score: 40% avg progress + 60% avg risk score
    if avg_score:
        health_score = round((avg_progress * 0.4) + (avg_score * 0.6))
    else:
        health_score = avg_progress

    # Weakest areas — modules least completed across org
    all_module_ids = [m.id for m in db.query(LearningModule).filter(LearningModule.is_published == True).limit(10).all()]
    weak_modules = []
    for mid in all_module_ids:
        completions = db.query(UserProgress).filter(
            UserProgress.module_id == mid,
            UserProgress.user_id.in_(member_ids),
            UserProgress.status == "completed"
        ).count()
        module = db.query(LearningModule).filter(LearningModule.id == mid).first()
        if module and completions < len(members):
            weak_modules.append({
                "title": module.title,
                "slug": module.slug,
                "completion_rate": round((completions / len(members)) * 100) if members else 0,
            })

    weak_modules.sort(key=lambda x: x["completion_rate"])

    return {
        "org_name": org.name,
        "health_score": health_score,
        "avg_progress": avg_progress,
        "avg_risk_score": avg_score,
        "member_count": len(members),
        "total_completions": total_completions,
        "members": sorted(member_stats, key=lambda x: x["progress_percent"], reverse=True),
        "weakest_areas": weak_modules[:5],
    }
