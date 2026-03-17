from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User, Organisation
import openai
import json
import httpx
from datetime import datetime

router = APIRouter()

async def fetch_ncsc_headlines() -> list:
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get("https://www.ncsc.gov.uk/api/1/services/v1/report-rss-feed.xml")
            import xml.etree.ElementTree as ET
            root = ET.fromstring(r.text)
            items = []
            for item in root.findall(".//item")[:3]:
                title = item.findtext("title", "").strip()
                if title:
                    items.append(title)
            return items
    except:
        return ["AI-powered attacks increasing across UK financial sector", "Supply chain vulnerabilities remain top concern for UK businesses", "NCSC urges organisations to patch critical infrastructure systems"]


@router.get("/today")
async def get_threat_briefing(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not settings.OPENAI_API_KEY:
        raise HTTPException(503, "AI not configured")

    org = db.query(Organisation).filter(Organisation.id == current_user.organisation_id).first() if current_user.organisation_id else None
    sector = org.sector if org else "General Business"
    user_name = current_user.full_name or current_user.email.split("@")[0]

    headlines = await fetch_ncsc_headlines()
    today = datetime.now().strftime("%A %d %B %Y")

    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = f"""You are a UK cybersecurity threat analyst. Write a concise daily threat briefing for {user_name} who works in {sector}.

Today is {today}. Recent NCSC headlines: {json.dumps(headlines)}

Return ONLY valid JSON:
{{
  "date": "{today}",
  "threat_level": "LOW|MODERATE|HIGH|CRITICAL",
  "headline": "One-line summary of today's top threat (max 15 words)",
  "summary": "2-3 sentence executive summary of today's cyber threat landscape for {sector}",
  "top_threats": [
    {{"threat": "Threat name", "description": "One sentence description", "severity": "LOW|MEDIUM|HIGH"}}
  ],
  "action_of_the_day": "One specific action {sector} organisations should take today (max 20 words)",
  "sector_relevance": "One sentence on why this matters specifically for {sector}"
}}
Include exactly 3 top_threats. UK English. Be specific and actionable."""

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a UK cybersecurity analyst. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.7,
        )
        briefing = json.loads(response.choices[0].message.content)
        return briefing
    except Exception as e:
        raise HTTPException(500, f"Briefing generation failed: {str(e)}")
