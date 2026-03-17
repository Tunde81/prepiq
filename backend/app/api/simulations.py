from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, SimulationScenario, SimulationSession
from app.services.event_service import EventService

router = APIRouter()


@router.get("/scenarios")
async def list_scenarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    scenarios = db.query(SimulationScenario).filter(
        SimulationScenario.is_published == True
    ).all()

    result = []
    for s in scenarios:
        last_session = db.query(SimulationSession).filter(
            SimulationSession.user_id == current_user.id,
            SimulationSession.scenario_id == s.id,
            SimulationSession.status == "completed"
        ).order_by(SimulationSession.completed_at.desc()).first()

        result.append({
            "id": s.id,
            "title": s.title,
            "slug": s.slug,
            "description": s.description,
            "category": s.category,
            "difficulty": s.difficulty,
            "duration_minutes": s.duration_minutes,
            "objectives": s.objectives,
            "best_score": last_session.score if last_session else None,
            "completed": last_session is not None,
        })
    return result


@router.post("/scenarios/{scenario_id}/start")
async def start_simulation(
    scenario_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    scenario = db.query(SimulationScenario).filter(
        SimulationScenario.id == scenario_id, SimulationScenario.is_published == True
    ).first()
    if not scenario:
        raise HTTPException(404, "Scenario not found")

    db.query(SimulationSession).filter(
        SimulationSession.user_id == current_user.id,
        SimulationSession.scenario_id == scenario_id,
        SimulationSession.status == "active"
    ).update({"status": "abandoned"})

    session = SimulationSession(
        user_id=current_user.id,
        scenario_id=scenario_id,
        status="active",
        current_step=0,
        actions_taken=[],
        hints_used=0,
        started_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=2)
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    background_tasks.add_task(
        EventService.track_simulation_start,
        user_id=current_user.id,
        scenario_id=scenario_id,
        session_id=session.id,
        scenario_title=scenario.title,
    )

    return {
        "session_id": session.id,
        "scenario": {
            "id": scenario.id,
            "title": scenario.title,
            "description": scenario.description,
            "objectives": scenario.objectives,
            "steps": scenario.steps,
            "hints": scenario.hints,
        },
        "expires_at": session.expires_at,
    }


class SubmitActionRequest(BaseModel):
    session_id: int
    step: int
    action: str
    use_hint: bool = False


@router.post("/action")
async def submit_action(
    payload: SubmitActionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    session = db.query(SimulationSession).filter(
        SimulationSession.id == payload.session_id,
        SimulationSession.user_id == current_user.id,
        SimulationSession.status == "active"
    ).first()

    if not session:
        raise HTTPException(404, "Active session not found")

    if datetime.utcnow() > session.expires_at:
        session.status = "abandoned"
        db.commit()
        raise HTTPException(400, "Session expired")

    scenario = db.query(SimulationScenario).filter(
        SimulationScenario.id == session.scenario_id
    ).first()

    steps = scenario.steps or []
    current_step_data = steps[payload.step] if payload.step < len(steps) else None

    actions = list(session.actions_taken or [])
    actions.append({
        "step": payload.step,
        "action": payload.action,
        "timestamp": datetime.utcnow().isoformat(),
        "hint_used": payload.use_hint,
    })
    session.actions_taken = actions
    session.current_step = payload.step + 1

    if payload.use_hint:
        session.hints_used += 1

    feedback = current_step_data.get("feedback", "Action recorded.") if current_step_data else "Action recorded."
    is_correct = payload.action in (current_step_data.get("correct_actions", []) if current_step_data else [])

    # Log step trace to MongoDB
    background_tasks.add_task(
        EventService.log_simulation_step,
        session_id=payload.session_id,
        user_id=current_user.id,
        scenario_id=session.scenario_id,
        step=payload.step,
        action=payload.action,
        is_correct=is_correct,
        hint_used=payload.use_hint,
    )

    # Check if simulation complete
    if session.current_step >= len(steps):
        correct_actions = sum(1 for a in actions if a.get("hint_used") == False)
        base_score = int((correct_actions / max(len(steps), 1)) * 100)
        hint_penalty = session.hints_used * 5
        final_score = max(0, base_score - hint_penalty)

        session.status = "completed"
        session.score = final_score
        session.completed_at = datetime.utcnow()
        db.commit()

        background_tasks.add_task(
            EventService.track_simulation_complete,
            user_id=current_user.id,
            scenario_id=session.scenario_id,
            session_id=session.id,
            score=final_score,
            hints_used=session.hints_used,
        )

        return {
            "completed": True,
            "score": final_score,
            "hints_used": session.hints_used,
            "feedback": "Simulation complete! Well done.",
        }

    db.commit()

    hint = None
    if payload.use_hint and scenario.hints:
        hints = scenario.hints
        hint = hints[payload.step] if payload.step < len(hints) else "No hint available."

    return {
        "completed": False,
        "next_step": session.current_step,
        "feedback": feedback,
        "is_correct": is_correct,
        "hint": hint,
    }
