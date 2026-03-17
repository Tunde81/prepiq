from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import openai
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User, LearningModule, UserProgress

router = APIRouter()

ROLES = [
    "C-Suite Executive (CEO/CFO/COO)",
    "IT Manager / IT Director",
    "Security Analyst / SOC Analyst",
    "Developer / Software Engineer",
    "SME Owner / Manager",
    "HR / People Manager",
    "Finance / Accounts",
    "Legal / Compliance Officer",
    "Council / Public Sector Worker",
    "General Staff / End User",
]

SECTORS = [
    "Financial Services / Banking",
    "Healthcare / NHS",
    "Legal Services",
    "Education",
    "Retail / E-commerce",
    "Local Government / Council",
    "Technology / SaaS",
    "Manufacturing",
    "Professional Services",
    "Charity / Non-profit",
]

class PathRequest(BaseModel):
    role: str
    sector: str
    experience_level: str = "beginner"

@router.get("/roles")
async def get_roles():
    return {"roles": ROLES, "sectors": SECTORS}

@router.post("/generate")
async def generate_learning_path(
    payload: PathRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(503, "AI not configured")

    # Get all available modules
    modules = db.query(LearningModule).filter(LearningModule.is_published == True).all()
    module_list = [{"id": m.id, "title": m.title, "slug": m.slug, "category": m.category, "difficulty": m.difficulty} for m in modules]

    # Get completed modules
    completed = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.status == "completed"
    ).all()
    completed_ids = {p.module_id for p in completed}

    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    prompt = f"""You are a UK cybersecurity training expert. Create a personalised learning path for:
- Role: {payload.role}
- Sector: {payload.sector}
- Experience Level: {payload.experience_level}

Available modules (select 8-10 most relevant, in recommended order):
{json.dumps(module_list, indent=2)}

Return ONLY valid JSON:
{{
  "path_title": "Descriptive path title",
  "path_description": "2 sentence description of why this path suits this role",
  "estimated_hours": number,
  "priority_focus": "Key area to focus on (1 sentence)",
  "modules": [
    {{"id": module_id, "reason": "Why this module matters for this role (1 sentence)"}}
  ]
}}

Rules:
- Order modules from most critical to nice-to-have
- Prioritise compliance modules relevant to their sector
- UK context throughout
- Select exactly 8-10 modules"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a UK cybersecurity curriculum expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7,
        )
        path_data = json.loads(response.choices[0].message.content)

        # Enrich with module details and completion status
        enriched_modules = []
        for i, item in enumerate(path_data["modules"]):
            module = next((m for m in modules if m.id == item["id"]), None)
            if module:
                enriched_modules.append({
                    "id": module.id,
                    "title": module.title,
                    "slug": module.slug,
                    "difficulty": module.difficulty,
                    "duration_minutes": module.duration_minutes,
                    "reason": item.get("reason", ""),
                    "completed": module.id in completed_ids,
                    "order": i + 1,
                })

        completed_in_path = sum(1 for m in enriched_modules if m["completed"])
        percent = round((completed_in_path / len(enriched_modules)) * 100) if enriched_modules else 0
        next_module = next((m for m in enriched_modules if not m["completed"]), None)

        return {
            "path_title": path_data["path_title"],
            "path_description": path_data["path_description"],
            "estimated_hours": path_data.get("estimated_hours", 4),
            "priority_focus": path_data.get("priority_focus", ""),
            "role": payload.role,
            "sector": payload.sector,
            "modules": enriched_modules,
            "percent_complete": percent,
            "completed_count": completed_in_path,
            "total_count": len(enriched_modules),
            "next_module": next_module,
        }
    except Exception as e:
        raise HTTPException(500, f"Path generation failed: {str(e)}")
