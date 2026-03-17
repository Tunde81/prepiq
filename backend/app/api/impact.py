from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User, UserProgress, LearningModule, RiskAssessment, Organisation, SimulationSession
from datetime import datetime

router = APIRouter()

@router.get("/stats")
async def get_impact_stats(db: Session = Depends(get_db)):
    total_users = db.query(User).filter(User.is_active == True).count()
    total_modules = db.query(LearningModule).filter(LearningModule.is_published == True).count()
    total_completions = db.query(UserProgress).filter(UserProgress.status == "completed").count()
    total_assessments = db.query(RiskAssessment).count()
    total_orgs = db.query(Organisation).filter(Organisation.is_active == True).count()
    total_lessons = total_modules * 4
    total_quiz_questions = total_modules * 5
    hours_of_content = round(total_modules * 0.5, 1)

    return {
        "users_trained": total_users,
        "modules_available": total_modules,
        "lessons_available": total_lessons,
        "quiz_questions": total_quiz_questions,
        "module_completions": total_completions,
        "risk_assessments": total_assessments,
        "organisations": total_orgs,
        "hours_of_content": hours_of_content,
        "frameworks_covered": 5,
        "uk_focus": True,
        "last_updated": datetime.utcnow().isoformat(),
    }
