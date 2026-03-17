"""
PrepIQ - Notifications Router
Admin endpoints to trigger bulk reminders
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


# ── Admin: Send reminders ─────────────────────────────────────────────────────

@router.post("/admin/send-reminders")
async def send_reminders(
    background_tasks: BackgroundTasks,
    reminder_type: str = "weekly",  # weekly | assessment
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send bulk reminders to all active users. Admin only."""
    if current_user.role.value not in ["superadmin", "admin"]:
        raise HTTPException(status_code=403, detail="Admin only")

    from app.models.user import User as UserModel, UserProgress
    from app.services.notification_service import notify_weekly_reminder, notify_assessment_reminder
    from app.features.health_index_models import HealthIndexAssessment, AssessmentStatus
    from sqlalchemy import and_
    from datetime import datetime, timezone, timedelta

    users = db.query(UserModel).filter_by(is_active=True, is_verified=True).all()
    sent = 0

    for user in users:
        if not user.email:
            continue
        if reminder_type == "weekly":
            completed_count = db.query(UserProgress).filter_by(
                user_id=user.id, status="completed"
            ).count()
            background_tasks.add_task(
                notify_weekly_reminder,
                user_email=user.email,
                user_name=user.full_name or user.email,
                modules_completed=completed_count,
            )
            sent += 1
        elif reminder_type == "assessment":
            latest = db.query(HealthIndexAssessment).filter(
                and_(
                    HealthIndexAssessment.org_id == user.organisation_id,
                    HealthIndexAssessment.status == AssessmentStatus.COMPLETED
                )
            ).order_by(HealthIndexAssessment.completed_at.desc()).first()

            days_since = None
            last_completed_str = None
            if latest and latest.completed_at:
                days_since = (datetime.now(timezone.utc) - latest.completed_at).days
                last_completed_str = latest.completed_at.strftime("%d %B %Y")
                if days_since < 60:
                    continue  # Skip if assessed recently

            background_tasks.add_task(
                notify_assessment_reminder,
                user_email=user.email,
                user_name=user.full_name or user.email,
                last_completed=last_completed_str,
                days_since=days_since,
            )
            sent += 1

    return {"message": f"Queued {sent} {reminder_type} reminders"}
