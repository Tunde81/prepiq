from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.notification_service import notify_badge_earned
from app.core.security import get_current_user
from app.models.user import User, UserBadge, UserProgress, RiskAssessment, SimulationSession

router = APIRouter()

BADGES = [
    {"id": "first_steps", "name": "First Steps", "icon": "🎯", "description": "Complete your first learning module"},
    {"id": "on_a_roll", "name": "On a Roll", "icon": "🔥", "description": "Complete 3 learning modules"},
    {"id": "cyber_scholar", "name": "Cyber Scholar", "icon": "🎓", "description": "Complete 5 learning modules"},
    {"id": "knowledge_seeker", "name": "Knowledge Seeker", "icon": "📚", "description": "Complete 10 learning modules"},
    {"id": "cyber_expert", "name": "Cyber Expert", "icon": "🏆", "description": "Complete 20 learning modules"},
    {"id": "risk_aware", "name": "Risk Aware", "icon": "🛡️", "description": "Complete your first risk assessment"},
    {"id": "simulator", "name": "Simulator", "icon": "🎮", "description": "Complete your first simulation"},
    {"id": "sim_veteran", "name": "Sim Veteran", "icon": "⚔️", "description": "Complete 3 simulations"},
    {"id": "uk_compliant", "name": "UK Compliant", "icon": "🇬🇧", "description": "Complete GDPR and Cyber Essentials modules"},
    {"id": "fintech_ready", "name": "FinTech Ready", "icon": "💳", "description": "Complete DORA and FCA modules"},
    {"id": "prepiq_elite", "name": "PrepIQ Elite", "icon": "🌟", "description": "Complete 20+ modules and a risk assessment"},
]


def check_and_award_badges(user_id: int, db: Session) -> list:
    earned = {b.badge_id for b in db.query(UserBadge).filter(UserBadge.user_id == user_id).all()}
    completed = db.query(UserProgress).filter(UserProgress.user_id == user_id, UserProgress.status == "completed").all()
    completed_ids = {p.module_id for p in completed}
    completed_count = len(completed)
    new_badges = []

    def award(badge_id):
        if badge_id not in earned:
            b = next((b for b in BADGES if b["id"] == badge_id), None)
            if b:
                db.add(UserBadge(user_id=user_id, badge_id=b["id"], badge_name=b["name"], badge_description=b["description"], badge_icon=b["icon"]))
                new_badges.append(b)
                earned.add(badge_id)

    if completed_count >= 1: award("first_steps")
    if completed_count >= 3: award("on_a_roll")
    if completed_count >= 5: award("cyber_scholar")
    if completed_count >= 10: award("knowledge_seeker")
    if completed_count >= 20: award("cyber_expert")

    assessments = db.query(RiskAssessment).filter(RiskAssessment.user_id == user_id).count()
    if assessments >= 1: award("risk_aware")

    sims = db.query(SimulationSession).filter(SimulationSession.user_id == user_id, SimulationSession.status == "completed").count()
    if sims >= 1: award("simulator")
    if sims >= 3: award("sim_veteran")

    # UK compliance badge - check for GDPR and Cyber Essentials modules
    from app.models.user import LearningModule
    gdpr_modules = db.query(LearningModule).filter(LearningModule.slug.ilike("%gdpr%")).all()
    ce_modules = db.query(LearningModule).filter(LearningModule.slug.ilike("%cyber-essentials%")).all()
    gdpr_done = any(m.id in completed_ids for m in gdpr_modules)
    ce_done = any(m.id in completed_ids for m in ce_modules)
    if gdpr_done and ce_done: award("uk_compliant")

    # FinTech badge - DORA and FCA modules
    dora_modules = db.query(LearningModule).filter(LearningModule.slug.ilike("%dora%")).all()
    fca_modules = db.query(LearningModule).filter(LearningModule.slug.ilike("%fca%")).all()
    dora_done = any(m.id in completed_ids for m in dora_modules)
    fca_done = any(m.id in completed_ids for m in fca_modules)
    if dora_done and fca_done: award("fintech_ready")

    if completed_count >= 20 and assessments >= 1: award("prepiq_elite")

    if new_badges:
        db.commit()
    return new_badges


@router.get("/my")
async def get_my_badges(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    badges = db.query(UserBadge).filter(UserBadge.user_id == current_user.id).order_by(UserBadge.earned_at).all()
    earned_ids = {b.badge_id for b in badges}
    all_badges = []
    for b in BADGES:
        earned = b["id"] in earned_ids
        earned_at = next((ub.earned_at.isoformat() for ub in badges if ub.badge_id == b["id"]), None)
        all_badges.append({**b, "earned": earned, "earned_at": earned_at})
    return {"badges": all_badges, "earned_count": len(earned_ids), "total": len(BADGES)}


@router.post("/check")
async def check_badges(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_badges = check_and_award_badges(current_user.id, db)
    total_badges = db.query(UserBadge).filter(UserBadge.user_id == current_user.id).count()
    for badge in new_badges:
        background_tasks.add_task(
            notify_badge_earned,
            user_email=current_user.email,
            user_name=current_user.full_name or current_user.email,
            badge_icon=badge["icon"],
            badge_name=badge["name"],
            badge_description=badge["description"],
            total_badges=total_badges,
        )
    return {"new_badges": new_badges, "count": len(new_badges)}
