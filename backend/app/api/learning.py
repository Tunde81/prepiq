from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.email_service import send_email, completion_email_html
from app.services.notification_service import notify_course_completion, notify_badge_earned
from app.models.user import User, LearningModule, Lesson, Quiz, UserProgress
from app.services.event_service import EventService

router = APIRouter()


# ─── MODULES ──────────────────────────────────────────────────────────────────

@router.get("/modules")
async def list_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    modules = db.query(LearningModule).filter(LearningModule.is_published == True).order_by(LearningModule.order_index).all()
    result = []
    for m in modules:
        progress = db.query(UserProgress).filter(
            UserProgress.user_id == current_user.id,
            UserProgress.module_id == m.id
        ).first()
        result.append({
            "id": m.id,
            "title": m.title,
            "slug": m.slug,
            "description": m.description,
            "category": m.category,
            "difficulty": m.difficulty,
            "duration_minutes": m.duration_minutes,
            "thumbnail_url": m.thumbnail_url,
            "progress": {
                "status": progress.status if progress else "not_started",
                "percent": progress.progress_percent if progress else 0,
                "quiz_score": progress.quiz_score if progress else None,
            }
        })
    return result


@router.get("/modules/{slug}")
async def get_module(
    slug: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    module = db.query(LearningModule).filter(
        LearningModule.slug == slug, LearningModule.is_published == True
    ).first()
    if not module:
        raise HTTPException(404, "Module not found")

    lessons = db.query(Lesson).filter(Lesson.module_id == module.id).order_by(Lesson.order_index).all()
    quizzes = db.query(Quiz).filter(Quiz.module_id == module.id).all()

    return {
        "id": module.id,
        "title": module.title,
        "slug": module.slug,
        "description": module.description,
        "category": module.category,
        "difficulty": module.difficulty,
        "duration_minutes": module.duration_minutes,
        "content": module.content,
        "lessons": [{"id": l.id, "title": l.title, "content": l.content, "duration_minutes": l.duration_minutes} for l in lessons],
        "quizzes": [{"id": q.id, "title": q.title, "pass_threshold": q.pass_threshold} for q in quizzes],
    }


# ─── PROGRESS ─────────────────────────────────────────────────────────────────

class StartModuleRequest(BaseModel):
    module_id: int


@router.post("/progress/start")
async def start_module(
    payload: StartModuleRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.module_id == payload.module_id
    ).first()

    if existing:
        return {"message": "Already started", "progress": existing.status}

    progress = UserProgress(
        user_id=current_user.id,
        module_id=payload.module_id,
        status="in_progress",
        progress_percent=0,
        started_at=datetime.utcnow()
    )
    db.add(progress)
    db.commit()

    module = db.query(LearningModule).filter(LearningModule.id == payload.module_id).first()
    background_tasks.add_task(
        EventService.track_module_start,
        user_id=current_user.id,
        module_id=payload.module_id,
        module_slug=module.slug if module else "",
    )

    return {"message": "Module started", "progress": "in_progress"}


class UpdateProgressRequest(BaseModel):
    module_id: int
    lesson_id: int
    progress_percent: int


@router.put("/progress/update")
async def update_progress(
    payload: UpdateProgressRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.module_id == payload.module_id
    ).first()

    if not progress:
        raise HTTPException(404, "Progress record not found")

    progress.last_lesson_id = payload.lesson_id
    progress.progress_percent = payload.progress_percent

    if payload.progress_percent >= 100:
        progress.status = "completed"
        progress.completed_at = datetime.utcnow()

    db.commit()
    return {"message": "Progress updated", "percent": payload.progress_percent}


# ─── QUIZZES ──────────────────────────────────────────────────────────────────

@router.get("/quiz/{quiz_id}")
async def get_quiz(
    quiz_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    # Return questions without correct answers
    safe_questions = []
    for q in quiz.questions:
        safe_questions.append({
            "question": q["question"],
            "options": q["options"],
        })

    return {
        "id": quiz.id,
        "title": quiz.title,
        "pass_threshold": quiz.pass_threshold,
        "questions": safe_questions,
    }


class SubmitQuizRequest(BaseModel):
    quiz_id: int
    answers: list[int]  # selected option indices


@router.post("/quiz/submit")
async def submit_quiz(
    payload: SubmitQuizRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    quiz = db.query(Quiz).filter(Quiz.id == payload.quiz_id).first()
    if not quiz:
        raise HTTPException(404, "Quiz not found")

    correct = 0
    results = []
    for i, question in enumerate(quiz.questions):
        user_answer = payload.answers[i] if i < len(payload.answers) else -1
        is_correct = user_answer == question["correct_index"]
        if is_correct:
            correct += 1
        results.append({
            "correct": is_correct,
            "explanation": question.get("explanation", ""),
            "correct_index": question["correct_index"],
        })

    score = int((correct / len(quiz.questions)) * 100)
    passed = score >= quiz.pass_threshold

    # Update progress
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.module_id == quiz.module_id
    ).first()
    if progress:
        progress.quiz_score = score

    db.commit()

    background_tasks.add_task(
        EventService.track_quiz_submit,
        user_id=current_user.id,
        quiz_id=quiz.id,
        module_id=quiz.module_id,
        score=score,
        passed=passed,
    )

    return {
        "score": score,
        "passed": passed,
        "correct": correct,
        "total": len(quiz.questions),
        "results": results,
    }
