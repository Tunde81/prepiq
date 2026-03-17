from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.user import User, LearningModule, SimulationScenario, AssessmentDomain, AssessmentQuestion

router = APIRouter()


# ─── MODULES CRUD ─────────────────────────────────────────────────────────────

class ModuleCreate(BaseModel):
    title: str
    slug: str
    description: str
    category: str
    difficulty: str
    duration_minutes: int = 15
    order_index: int = 0
    is_published: bool = False
    content: Optional[dict] = None
    thumbnail_url: Optional[str] = None


@router.get("/modules")
async def admin_list_modules(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return db.query(LearningModule).order_by(LearningModule.order_index).all()


@router.post("/modules", status_code=201)
async def admin_create_module(
    payload: ModuleCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    m = LearningModule(**payload.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return {"id": m.id, "title": m.title}


@router.put("/modules/{module_id}")
async def admin_update_module(
    module_id: int,
    payload: ModuleCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    m = db.query(LearningModule).filter(LearningModule.id == module_id).first()
    if not m:
        raise HTTPException(404, "Module not found")
    for k, v in payload.model_dump().items():
        setattr(m, k, v)
    db.commit()
    return {"message": "Updated"}


# ─── SCENARIOS CRUD ───────────────────────────────────────────────────────────

class ScenarioCreate(BaseModel):
    title: str
    slug: str
    description: str
    category: str
    difficulty: str
    duration_minutes: int = 20
    objectives: List[str] = []
    steps: List[dict] = []
    hints: List[str] = []
    is_published: bool = False


@router.get("/scenarios")
async def admin_list_scenarios(db: Session = Depends(get_db), _=Depends(get_current_admin)):
    return db.query(SimulationScenario).all()


@router.post("/scenarios", status_code=201)
async def admin_create_scenario(
    payload: ScenarioCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    s = SimulationScenario(**payload.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return {"id": s.id, "title": s.title}


# ─── USERS LIST ───────────────────────────────────────────────────────────────

@router.get("/users")
async def admin_list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return [{
        "id": u.id,
        "email": u.email,
        "full_name": u.full_name,
        "role": u.role,
        "is_active": u.is_active,
        "is_verified": u.is_verified,
        "created_at": u.created_at,
        "last_login": u.last_login,
    } for u in users]


@router.put("/scenarios/{scenario_id}")
async def admin_update_scenario(
    scenario_id: int,
    payload: ScenarioCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_admin)
):
    s = db.query(SimulationScenario).filter(SimulationScenario.id == scenario_id).first()
    if not s:
        raise HTTPException(404, "Scenario not found")
    for k, v in payload.model_dump().items():
        setattr(s, k, v)
    db.commit()
    return {"message": "Updated"}
