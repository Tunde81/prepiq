from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import openai

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User

router = APIRouter()

SYSTEM_PROMPT = """You are CyberCoach, an expert AI assistant for PrepIQ - the UK National Cyber Preparedness Learning Platform. You specialise in UK cybersecurity regulations (GDPR, NIS2, DORA, FCA, Cyber Essentials), common attack vectors, incident response (NIST, NCSC CAF), and security awareness for SMEs. Be concise, practical, use UK spelling, and never provide advice that could be used maliciously. Direct active incident queries to ncsc.gov.uk and Action Fraud."""

class ChatMessage(BaseModel):
    role: str
    content: str

class CoachRequest(BaseModel):
    message: str
    context: Optional[str] = None
    history: list[ChatMessage] = []

@router.post("/chat")
async def chat_with_coach(payload: CoachRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(503, "AI Coach is not configured")
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    context_note = f"\n\n[User context: {payload.context}]" if payload.context else ""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in payload.history[-10:]:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": payload.message + context_note})
    try:
        response = await client.chat.completions.create(model="gpt-4o-mini", messages=messages, max_tokens=600, temperature=0.7)
        return {"reply": response.choices[0].message.content, "tokens_used": response.usage.total_tokens}
    except openai.AuthenticationError:
        raise HTTPException(503, "AI Coach authentication failed")
    except openai.RateLimitError:
        raise HTTPException(429, "AI Coach is busy - please try again in a moment")
    except Exception as e:
        raise HTTPException(500, f"AI Coach error: {str(e)}")

@router.get("/status")
async def coach_status(current_user: User = Depends(get_current_user)):
    return {"available": bool(settings.OPENAI_API_KEY), "model": "gpt-4o-mini"}


class GenerateRequest(BaseModel):
    topic: str
    type: str = "module"  # "module" or "scenario"

@router.post("/generate")
async def generate_content(payload: GenerateRequest, current_user: User = Depends(get_current_user)):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(503, "AI generation not configured")
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    if payload.type == "module":
        prompt = f"""Generate a cybersecurity learning module for the topic: "{payload.topic}"
Return ONLY valid JSON with these exact fields:
{{
  "title": "concise module title",
  "slug": "url-friendly-slug",
  "description": "2-3 sentence description",
  "category": "one of: awareness, technical, compliance, incident-response",
  "difficulty": "one of: beginner, intermediate, advanced",
  "duration_minutes": number between 10-45,
  "objectives": ["objective 1", "objective 2", "objective 3"]
}}"""
    else:
        prompt = f"""Generate a cybersecurity simulation scenario for the topic: "{payload.topic}"
Return ONLY valid JSON with these exact fields:
{{
  "title": "concise scenario title",
  "slug": "url-friendly-slug",
  "description": "2-3 sentence description",
  "category": "one of: phishing, ransomware, cloud, social-engineering, incident-response",
  "difficulty": "one of: beginner, intermediate, advanced",
  "duration_minutes": number between 15-60,
  "objectives": ["objective 1", "objective 2", "objective 3"],
  "hints": ["hint 1", "hint 2", "hint 3"]
}}"""
    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a UK cybersecurity curriculum expert. Always respond with valid JSON only, no markdown or extra text."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7,
        )
        import json
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        raise HTTPException(500, f"Generation failed: {str(e)}")


class GenerateLessonsRequest(BaseModel):
    module_id: int
    topic: str
    num_lessons: int = 4

@router.post("/generate-lessons")
async def generate_lessons(payload: GenerateLessonsRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(503, "AI generation not configured")
    from app.models.user import LearningModule, Lesson
    module = db.query(LearningModule).filter(LearningModule.id == payload.module_id).first()
    if not module:
        raise HTTPException(404, "Module not found")
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = f"""Create {payload.num_lessons} detailed cybersecurity lessons for a module titled "{payload.topic}".
Return ONLY valid JSON array with this exact structure:
[
  {{
    "title": "Lesson title",
    "order_index": 1,
    "content": "Full lesson content in markdown format with ## headings, bullet points, and practical examples. Minimum 300 words. UK spelling."
  }}
]
Make lessons progressive - start with fundamentals, build to practical application. UK context and examples."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a UK cybersecurity curriculum expert. Return only valid JSON, no markdown fences."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            temperature=0.7,
        )
        import json
        lessons_data = json.loads(response.choices[0].message.content)
        created = []
        for i, lesson in enumerate(lessons_data):
            l = Lesson(
                module_id=module.id,
                title=lesson["title"],
                content=lesson["content"],
                order_index=lesson.get("order_index", i + 1),
            )
            db.add(l)
            created.append(lesson["title"])
        db.commit()
        return {"created": len(created), "lessons": created}
    except Exception as e:
        raise HTTPException(500, f"Lesson generation failed: {str(e)}")


class GenerateQuizRequest(BaseModel):
    module_id: int
    num_questions: int = 5

@router.post("/generate-quiz")
async def generate_quiz(payload: GenerateQuizRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(503, "AI generation not configured")
    from app.models.user import LearningModule, Quiz, Lesson
    module = db.query(LearningModule).filter(LearningModule.id == payload.module_id).first()
    if not module:
        raise HTTPException(404, "Module not found")

    # Get lesson content for context
    lessons = db.query(Lesson).filter(Lesson.module_id == module.id).all()
    context = " ".join([l.content[:500] for l in lessons[:3]]) if lessons else module.description

    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = f"""Create {payload.num_questions} multiple choice quiz questions for a cybersecurity module titled "{module.title}".
Base questions on this content: {context[:1500]}

Return ONLY valid JSON array:
[
  {{
    "question": "Clear question text?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,
    "explanation": "Brief explanation of why this is correct. UK spelling."
  }}
]
Rules:
- correct_index is 0-3 (index of correct option in options array)
- Mix difficulty levels
- Make distractors plausible
- Use UK spelling and context
- No trick questions"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a UK cybersecurity assessment expert. Return only valid JSON, no markdown fences."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7,
        )
        import json
        questions = json.loads(response.choices[0].message.content)

        # Delete existing quiz for this module if any
        existing = db.query(Quiz).filter(Quiz.module_id == module.id).first()
        if existing:
            db.delete(existing)
            db.flush()

        quiz = Quiz(
            module_id=module.id,
            title=f"{module.title} - Knowledge Check",
            questions=questions,
            pass_threshold=70,
        )
        db.add(quiz)
        db.commit()
        return {"created": len(questions), "quiz_id": quiz.id, "title": quiz.title}
    except Exception as e:
        raise HTTPException(500, f"Quiz generation failed: {str(e)}")
