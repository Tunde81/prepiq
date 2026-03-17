from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user, get_current_admin
from app.models.user import User, UserProgress, RiskAssessment, SimulationSession, LearningModule
from app.services.event_service import EventService

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    progress_records = db.query(UserProgress).filter(UserProgress.user_id == current_user.id).all()
    completed_modules = sum(1 for p in progress_records if p.status == "completed")
    in_progress_modules = sum(1 for p in progress_records if p.status == "in_progress")

    completed_simulations = db.query(SimulationSession).filter(
        SimulationSession.user_id == current_user.id,
        SimulationSession.status == "completed"
    ).count()

    avg_sim_score = db.query(func.avg(SimulationSession.score)).filter(
        SimulationSession.user_id == current_user.id,
        SimulationSession.status == "completed"
    ).scalar()

    latest_assessment = db.query(RiskAssessment).filter(
        RiskAssessment.user_id == current_user.id
    ).order_by(RiskAssessment.created_at.desc()).first()

    total_modules = db.query(LearningModule).filter(LearningModule.is_published == True).count()

    # Recent activity from MongoDB (non-fatal if unavailable)
    recent_events = await EventService.get_user_recent_events(current_user.id, limit=10)

    return {
        "learning": {
            "completed_modules": completed_modules,
            "in_progress_modules": in_progress_modules,
            "total_modules": total_modules,
            "completion_rate": round((completed_modules / total_modules * 100) if total_modules else 0, 1),
        },
        "simulations": {
            "completed": completed_simulations,
            "avg_score": round(avg_sim_score or 0, 1),
        },
        "assessment": {
            "latest_score": latest_assessment.overall_score if latest_assessment else None,
            "maturity_level": latest_assessment.maturity_level if latest_assessment else None,
            "last_run": latest_assessment.created_at if latest_assessment else None,
        },
        "recent_activity": [
            {
                "event_type": e.get("event_type"),
                "timestamp": e.get("timestamp"),
                "metadata": e.get("metadata", {}),
            }
            for e in recent_events
        ],
    }


@router.get("/activity")
async def get_my_activity(current_user: User = Depends(get_current_user)):
    """Returns the current user's last 50 events from MongoDB."""
    events = await EventService.get_user_recent_events(current_user.id, limit=50)
    return [{
        "event_type": e.get("event_type"),
        "timestamp": e.get("timestamp"),
        "metadata": e.get("metadata", {}),
    } for e in events]


@router.get("/simulation/{session_id}/trace")
async def get_simulation_trace(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns the full step trace for a simulation session from MongoDB."""
    # Verify ownership
    session = db.query(SimulationSession).filter(
        SimulationSession.id == session_id,
        SimulationSession.user_id == current_user.id
    ).first()
    if not session:
        from fastapi import HTTPException
        raise HTTPException(404, "Session not found")

    trace = await EventService.get_simulation_trace(session_id)
    return {"session_id": session_id, "steps": trace}


@router.get("/admin/platform")
async def get_platform_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_assessments = db.query(RiskAssessment).count()
    avg_score = db.query(func.avg(RiskAssessment.overall_score)).scalar()
    total_completions = db.query(UserProgress).filter(UserProgress.status == "completed").count()
    total_simulations = db.query(SimulationSession).filter(SimulationSession.status == "completed").count()

    # Event counts from MongoDB
    from datetime import datetime, timezone, timedelta
    since_30d = datetime.now(timezone.utc) - timedelta(days=30)
    logins_30d = await EventService.count_events_by_type("login", since=since_30d)
    completions_30d = await EventService.count_events_by_type("module_complete", since=since_30d)

    return {
        "users": {"total": total_users, "active": active_users},
        "assessments": {"total": total_assessments, "avg_score": round(avg_score or 0, 1)},
        "learning": {"module_completions": total_completions},
        "simulations": {"completed": total_simulations},
        "last_30_days": {
            "logins": logins_30d,
            "module_completions": completions_30d,
        }
    }
