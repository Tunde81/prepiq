"""
PrepIQ - Cyber Incident Simulator Router
Endpoints: scenario library, session management, decision scoring,
           timed challenge grading, AI debrief (via CyberCoach), leaderboard
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import json
import httpx
import os

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from .simulator_models import (
    IncidentScenario, IncidentSimulationSession, SimulatorLeaderboard,
    SimulatorMode, SessionStatus, ScenarioCategory, DifficultyLevel
)

router = APIRouter(prefix="/api/simulator", tags=["simulator"])

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


# ─────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────

class SessionStart(BaseModel):
    scenario_id: int
    mode: SimulatorMode


class DecisionSubmit(BaseModel):
    phase_id: str
    choice_id: str
    rationale: Optional[str] = None


class ChallengeAnswer(BaseModel):
    challenge_id: str
    answer: str
    time_taken_seconds: int


class DebriefMessage(BaseModel):
    message: str


# ─────────────────────────────────────────────
# Scoring logic
# ─────────────────────────────────────────────

def score_decision(choice_id: str, phase: dict) -> float:
    """Score a tabletop decision choice: optimal=1.0, acceptable=0.5, poor=0.0"""
    for choice in phase.get("choices", []):
        if choice["id"] == choice_id:
            return float(choice.get("score", 0.5))
    return 0.0


def grade_challenge(answer: str, challenge: dict) -> bool:
    """Simple exact/fuzzy match for timed challenge answers."""
    answer_key = challenge.get("answer_key", "").lower().strip()
    given = answer.lower().strip()
    # Exact match, or answer is contained in key or vice versa
    return given == answer_key or given in answer_key or answer_key in given


def compute_session_score(session: IncidentSimulationSession, scenario: IncidentScenario) -> dict:
    decision_score = None
    speed_score = None

    # Tabletop decision score
    if session.decisions:
        phases_map = {p["phase_id"]: p for p in scenario.phases}
        total, earned = 0, 0
        for dec in session.decisions:
            phase = phases_map.get(dec["phase_id"])
            if phase:
                s = score_decision(dec["choice_id"], phase)
                earned += s
                total += 1
        decision_score = round((earned / total) * 100, 1) if total else None

    # Timed challenge speed score
    if session.challenge_results:
        challenges_map = {c["challenge_id"]: c for c in (scenario.timed_challenges or [])}
        correct = sum(1 for r in session.challenge_results if r.get("correct"))
        total_ch = len(session.challenge_results)
        base = (correct / total_ch) * 80 if total_ch else 0
        # Speed bonus: up to +20 pts based on total time vs expected
        total_time = sum(r.get("time_taken", 999) for r in session.challenge_results)
        expected = sum(c.get("time_limit_seconds", 120) for c in (scenario.timed_challenges or []))
        if expected > 0:
            time_ratio = max(0, 1 - (total_time / expected))
            speed_bonus = time_ratio * 20
        else:
            speed_bonus = 0
        speed_score = round(min(100, base + speed_bonus), 1)

    scores = [s for s in [decision_score, speed_score] if s is not None]
    overall = round(sum(scores) / len(scores), 1) if scores else None

    return {
        "overall_score": overall,
        "decision_score": decision_score,
        "speed_score": speed_score,
    }


# ─────────────────────────────────────────────
# Routes: Scenario library
# ─────────────────────────────────────────────

@router.get("/scenarios")
def list_scenarios(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(IncidentScenario).filter_by(is_active=True)
    if category:
        q = q.filter_by(category=category)
    if difficulty:
        q = q.filter_by(difficulty=difficulty)
    scenarios = q.all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "category": s.category.value,
            "difficulty": s.difficulty.value,
            "synopsis": s.synopsis,
            "estimated_minutes": s.estimated_minutes,
            "frameworks": s.frameworks,
            "learning_objectives": s.learning_objectives,
            "phase_count": len(s.phases) if s.phases else 0,
            "has_challenges": bool(s.timed_challenges),
        }
        for s in scenarios
    ]


@router.get("/scenarios/{scenario_id}")
def get_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    s = db.query(IncidentScenario).filter_by(id=scenario_id, is_active=True).first()
    if not s:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {
        "id": s.id, "title": s.title, "category": s.category.value,
        "difficulty": s.difficulty.value, "synopsis": s.synopsis,
        "context": s.context, "initial_inject": s.initial_inject,
        "phases": s.phases, "timed_challenges": s.timed_challenges,
        "learning_objectives": s.learning_objectives, "frameworks": s.frameworks,
        "estimated_minutes": s.estimated_minutes,
    }


# ─────────────────────────────────────────────
# Routes: Session lifecycle
# ─────────────────────────────────────────────

@router.post("/session/start")
def start_session(
    req: SessionStart,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    scenario = db.query(IncidentScenario).filter_by(id=req.scenario_id, is_active=True).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    session = IncidentSimulationSession(
        user_id=current_user.id,
        org_id=current_user.organisation_id,
        scenario_id=req.scenario_id,
        mode=req.mode,
        decisions=[],
        challenge_results=[],
        debrief_messages=[],
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "scenario": {
            "id": scenario.id, "title": scenario.title,
            "initial_inject": scenario.initial_inject,
            "phases": scenario.phases,
            "timed_challenges": scenario.timed_challenges,
            "context": scenario.context,
        }
    }


@router.post("/session/{session_id}/decision")
def submit_decision(
    session_id: int,
    req: DecisionSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record a tabletop scenario decision."""
    sim = db.query(IncidentSimulationSession).filter_by(id=session_id, user_id=current_user.id).first()
    if not sim or sim.status != SessionStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Active session not found")

    scenario = db.query(IncidentScenario).filter_by(id=sim.scenario_id).first()
    phases_map = {p["phase_id"]: p for p in scenario.phases}
    phase = phases_map.get(req.phase_id)
    if not phase:
        raise HTTPException(status_code=400, detail="Unknown phase")

    score = score_decision(req.choice_id, phase)

    decisions = list(sim.decisions or [])
    # Remove previous decision for this phase if re-answering
    decisions = [d for d in decisions if d["phase_id"] != req.phase_id]
    decisions.append({
        "phase_id": req.phase_id,
        "choice_id": req.choice_id,
        "rationale": req.rationale,
        "score": score,
        "timestamp": datetime.utcnow().isoformat(),
    })
    sim.decisions = decisions
    db.commit()

    # Return feedback for this choice
    choice_detail = next((c for c in phase.get("choices", []) if c["id"] == req.choice_id), {})
    return {
        "score": score,
        "feedback": choice_detail.get("feedback", ""),
        "consequence": choice_detail.get("consequence", ""),
        "optimal": score >= 1.0,
    }


@router.post("/session/{session_id}/challenge")
def submit_challenge(
    session_id: int,
    req: ChallengeAnswer,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Record a timed challenge answer."""
    sim = db.query(IncidentSimulationSession).filter_by(id=session_id, user_id=current_user.id).first()
    if not sim or sim.status != SessionStatus.ACTIVE:
        raise HTTPException(status_code=404, detail="Active session not found")

    scenario = db.query(IncidentScenario).filter_by(id=sim.scenario_id).first()
    challenge = next(
        (c for c in (scenario.timed_challenges or []) if c["challenge_id"] == req.challenge_id),
        None
    )
    if not challenge:
        raise HTTPException(status_code=400, detail="Unknown challenge")

    correct = grade_challenge(req.answer, challenge)
    results = list(sim.challenge_results or [])
    results = [r for r in results if r["challenge_id"] != req.challenge_id]
    results.append({
        "challenge_id": req.challenge_id,
        "answer": req.answer,
        "correct": correct,
        "time_taken": req.time_taken_seconds,
        "timestamp": datetime.utcnow().isoformat(),
    })
    sim.challenge_results = results
    db.commit()

    return {
        "correct": correct,
        "correct_answer": challenge.get("answer_key") if not correct else None,
        "explanation": challenge.get("explanation", ""),
    }


@router.post("/session/{session_id}/complete")
def complete_session(
    session_id: int,
    elapsed_seconds: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Finalise session, compute scores, update leaderboard."""
    sim = db.query(IncidentSimulationSession).filter_by(id=session_id, user_id=current_user.id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Session not found")

    scenario = db.query(IncidentScenario).filter_by(id=sim.scenario_id).first()
    scores = compute_session_score(sim, scenario)

    sim.overall_score = scores["overall_score"]
    sim.decision_score = scores["decision_score"]
    sim.speed_score = scores["speed_score"]
    sim.status = SessionStatus.COMPLETED
    sim.completed_at = datetime.utcnow()
    sim.elapsed_seconds = elapsed_seconds

    # Upsert leaderboard
    existing_lb = db.query(SimulatorLeaderboard).filter_by(
        scenario_id=sim.scenario_id, user_id=current_user.id
    ).first()
    if scores["overall_score"]:
        if not existing_lb or (scores["overall_score"] > existing_lb.overall_score):
            if existing_lb:
                existing_lb.overall_score = scores["overall_score"]
                existing_lb.elapsed_seconds = elapsed_seconds
                existing_lb.session_id = sim.id
                existing_lb.achieved_at = datetime.utcnow()
            else:
                lb = SimulatorLeaderboard(
                    scenario_id=sim.scenario_id, user_id=current_user.id,
                    session_id=sim.id, overall_score=scores["overall_score"],
                    elapsed_seconds=elapsed_seconds,
                )
                db.add(lb)

    db.commit()
    return {**scores, "session_id": session_id, "elapsed_seconds": elapsed_seconds}


# ─────────────────────────────────────────────
# AI Debrief (CyberCoach integration)
# ─────────────────────────────────────────────

DEBRIEF_SYSTEM_PROMPT = """You are CyberCoach, PrepIQ's AI incident response mentor. 
A user has just completed a cyber incident simulation exercise. Your role is to:
1. Debrief their decisions: acknowledge what they did well and what could improve
2. Ask probing questions to deepen their understanding (NIST CSF phases, NCSC guidance)
3. Reference real-world UK incidents, regulations (UK GDPR, FCA SYSC 13, DORA) where relevant
4. Be encouraging but honest — this is a professional learning environment
5. Suggest PrepIQ learning modules for gaps you identify

Keep responses concise (150–250 words). Use a direct, practitioner tone.
Do NOT use bullet points unless listing specific action items.
"""


@router.post("/session/{session_id}/debrief")
async def ai_debrief(
    session_id: int,
    req: DebriefMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Stream an AI debrief conversation response."""
    sim = db.query(IncidentSimulationSession).filter_by(id=session_id, user_id=current_user.id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="Session not found")

    scenario = db.query(IncidentScenario).filter_by(id=sim.scenario_id).first()

    # Build context for the AI
    context_block = f"""
SCENARIO: {scenario.title} ({scenario.category.value}, {scenario.difficulty.value})
SYNOPSIS: {scenario.synopsis}

USER PERFORMANCE:
- Overall Score: {sim.overall_score or 'Incomplete'}
- Decision Score: {sim.decision_score or 'N/A'}
- Speed Score: {sim.speed_score or 'N/A'}

DECISIONS MADE:
{json.dumps(sim.decisions or [], indent=2)}

CHALLENGE RESULTS:
{json.dumps(sim.challenge_results or [], indent=2)}
"""
    history = list(sim.debrief_messages or [])
    if not history:
        # Auto-open the debrief
        history.append({
            "role": "user",
            "content": f"I've just completed the '{scenario.title}' simulation. Here are my results:\n{context_block}\n\nPlease debrief me."
        })

    history.append({"role": "user", "content": req.message})

    # Prefer Anthropic API; fallback guidance if no key
    if not ANTHROPIC_API_KEY:
        fallback = f"[AI Debrief unavailable — set ANTHROPIC_API_KEY in environment]\n\nYour score: {sim.overall_score or 'N/A'}/100."
        history.append({"role": "assistant", "content": fallback})
        sim.debrief_messages = history
        db.commit()
        return {"response": fallback}

    async def stream_response():
        async with httpx.AsyncClient(timeout=30) as client:
            async with client.stream(
                "POST",
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-3-5-haiku-20241022",
                    "max_tokens": 600,
                    "system": DEBRIEF_SYSTEM_PROMPT,
                    "messages": history,
                    "stream": True,
                }
            ) as resp:
                full_text = ""
                async for line in resp.aiter_lines():
                    if line.startswith("data:"):
                        chunk = line[5:].strip()
                        if chunk == "[DONE]":
                            break
                        try:
                            data = json.loads(chunk)
                            if data.get("type") == "content_block_delta":
                                text = data["delta"].get("text", "")
                                full_text += text
                                yield text
                        except Exception:
                            pass
                # Persist conversation
                history.append({"role": "assistant", "content": full_text})
                sim.debrief_messages = history
                db.commit()

    return StreamingResponse(stream_response(), media_type="text/plain")


# ─────────────────────────────────────────────
# Leaderboard
# ─────────────────────────────────────────────

@router.get("/leaderboard/{scenario_id}")
def get_leaderboard(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    rows = db.query(SimulatorLeaderboard).filter_by(scenario_id=scenario_id)\
        .order_by(desc(SimulatorLeaderboard.overall_score)).limit(20).all()
    return [
        {
            "rank": i + 1,
            "user_id": r.user_id,
            "username": r.user.username if r.user else "Unknown",
            "overall_score": r.overall_score,
            "elapsed_seconds": r.elapsed_seconds,
            "achieved_at": r.achieved_at.strftime("%d %b %Y") if r.achieved_at else None,
            "is_current_user": r.user_id == current_user.id,
        }
        for i, r in enumerate(rows)
    ]


# ─────────────────────────────────────────────
# Admin: Seed scenarios
# ─────────────────────────────────────────────

@router.post("/admin/seed-scenarios")
def seed_scenarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.value not in ["superadmin", "admin"]:
        raise HTTPException(status_code=403, detail="Admin only")

    existing = db.query(IncidentScenario).count()
    if existing > 0:
        return {"message": f"Scenarios already seeded ({existing} found)"}

    scenarios = [
        {
            "title": "Ransomware: Friday Night Lock-Out",
            "category": ScenarioCategory.RANSOMWARE,
            "difficulty": DifficultyLevel.INTERMEDIATE,
            "synopsis": "A UK professional services firm discovers its file servers encrypted on a Friday evening. Staff cannot access client data. A ransom note demands £150,000 in Bitcoin within 48 hours.",
            "context": {"sector": "Professional Services", "employees": 85, "systems_affected": ["file server", "backup server", "3 workstations"]},
            "initial_inject": "It's 18:42 on a Friday. Your IT manager calls: 'All our shared drives are encrypted. There's a note on every machine saying they have 200GB of client data and want £150k by Sunday or they'll publish it.' Your MD is demanding answers. What do you do first?",
            "estimated_minutes": 35,
            "frameworks": ["NCSC CAF", "NIST CSF", "UK GDPR Art.33"],
            "learning_objectives": ["Activate incident response plan", "Assess scope and containment options", "Understand ICO 72-hour notification obligation", "Evaluate ransom payment risks"],
            "phases": [
                {
                    "phase_id": "p1",
                    "title": "Initial Response",
                    "inject": "The IT manager confirms ransomware has spread across your file server and potentially two backup drives. The attacker claims to have exfiltrated client PII. Your MD wants to call the ransom payers immediately.",
                    "choices": [
                        {"id": "c1a", "text": "Isolate all affected systems from the network immediately, even if it disrupts operations", "score": 1.0, "feedback": "Correct first move. Network isolation halts lateral spread and buys time to assess scope.", "consequence": "Operations pause but spread is contained. IT can now assess safely."},
                        {"id": "c1b", "text": "Keep systems running to preserve evidence and assess the scope first", "score": 0.3, "feedback": "Partial credit. While evidence matters, continued connection risks further spread and data exfiltration.", "consequence": "Two more workstations become encrypted during assessment."},
                        {"id": "c1c", "text": "Call the ransom number immediately to open negotiations", "score": 0.0, "feedback": "Never contact attackers as a first step. This reveals you're willing to engage and may escalate demands.", "consequence": "Attackers increase demand to £300k after the call."},
                    ]
                },
                {
                    "phase_id": "p2",
                    "title": "Notification Decision",
                    "inject": "It's now Saturday morning. You've confirmed client PII was likely accessed. Your legal team asks about notification obligations. The incident occurred approximately 36 hours ago.",
                    "choices": [
                        {"id": "c2a", "text": "Notify the ICO immediately — you've exceeded 24 hours and must report within 72 hours of becoming aware", "score": 1.0, "feedback": "Correct. UK GDPR Art.33 requires notification to the ICO within 72 hours of becoming aware of a personal data breach.", "consequence": "ICO acknowledges report. Demonstrates good faith compliance."},
                        {"id": "c2b", "text": "Wait until you know the full extent of the breach before notifying", "score": 0.25, "feedback": "The 72-hour clock runs from when you became aware, not when the investigation is complete. Waiting risks a fine.", "consequence": "You miss the 72-hour window. ICO investigation follows."},
                        {"id": "c2c", "text": "Only notify if you confirm data was definitely exfiltrated", "score": 0.1, "feedback": "Incorrect threshold. You must notify when there is a likely risk to individuals, not only confirmed exfiltration.", "consequence": "Enforcement action initiated for late notification."},
                    ]
                },
                {
                    "phase_id": "p3",
                    "title": "Recovery Strategy",
                    "inject": "Your backups are intact on a separate offline NAS. Restoring will take 18 hours. Paying the ransom might restore in 2 hours. Your MD is weighing the cost.",
                    "choices": [
                        {"id": "c3a", "text": "Restore from clean backups — rebuild systems from scratch if needed", "score": 1.0, "feedback": "Best practice. Paying ransoms funds criminal activity, doesn't guarantee decryption, and may make you a repeat target.", "consequence": "18-hour rebuild. Systems restored clean. NCSC notified."},
                        {"id": "c3b", "text": "Pay the ransom to restore quickly, then rebuild security afterwards", "score": 0.1, "feedback": "NCSC and NCUA strongly advise against paying. No guarantee of key delivery. Marks you as a payer for future attacks.", "consequence": "Payment made. Decryptor received but some files still corrupted. Second ransom demand follows."},
                        {"id": "c3c", "text": "Negotiate with attackers to reduce the ransom while restoring backups in parallel", "score": 0.4, "feedback": "Parallel recovery is sensible but negotiating still funds crime and distracts from clean recovery.", "consequence": "Backup restoration proceeds. Negotiation wastes 6 hours of IT resource."},
                    ]
                },
            ],
            "timed_challenges": [
                {
                    "challenge_id": "tc1",
                    "task": "Name the UK regulation that requires you to notify the data protection authority within 72 hours of a personal data breach.",
                    "time_limit_seconds": 45,
                    "hints": ["Think UK data protection law post-Brexit"],
                    "answer_key": "uk gdpr",
                    "explanation": "UK GDPR Article 33 mandates notification to the ICO within 72 hours of becoming aware of a personal data breach that poses a risk to individuals."
                },
                {
                    "challenge_id": "tc2",
                    "task": "What does the 3-2-1 backup rule stand for? (Format: 3 X, 2 Y, 1 Z)",
                    "time_limit_seconds": 60,
                    "hints": ["Copies, media types, offsite"],
                    "answer_key": "3 copies 2 media types 1 offsite",
                    "explanation": "3 copies of data, stored on 2 different media types, with 1 copy offsite (or air-gapped). This strategy survived this attack because the NAS was offline."
                },
                {
                    "challenge_id": "tc3",
                    "task": "What NIST CSF function covers detecting and responding to a cybersecurity event?",
                    "time_limit_seconds": 30,
                    "hints": ["Two of the five core functions"],
                    "answer_key": "detect and respond",
                    "explanation": "The NIST CSF five core functions are: Identify, Protect, Detect, Respond, Recover. Detection (monitoring) and Response (IR plan activation) are both triggered here."
                },
            ],
        },
        {
            "title": "BEC: The CEO's Wire Transfer",
            "category": ScenarioCategory.BUSINESS_EMAIL_COMPROMISE,
            "difficulty": DifficultyLevel.BEGINNER,
            "synopsis": "A finance officer at a UK SME receives an urgent email apparently from the CEO requesting a £47,000 international wire transfer for a confidential acquisition. The email looks legitimate.",
            "context": {"sector": "Manufacturing", "employees": 40, "target": "Finance Officer"},
            "initial_inject": "You're the Finance Manager. It's Tuesday at 15:30. You receive an email from 'ceo@yourcompany-secure.co.uk' (note the domain): 'Hi [name], I'm in meetings all afternoon — can you urgently process a £47k wire to Nexus Trading GmbH (IBAN: DE89...) for the acquisition? Keep confidential for now. I'll explain later. — James.' What do you do?",
            "estimated_minutes": 20,
            "frameworks": ["NCSC Phishing Guidance", "FCA SYSC 13"],
            "learning_objectives": ["Identify BEC red flags", "Apply out-of-band verification", "Understand financial controls for wire transfers"],
            "phases": [
                {
                    "phase_id": "p1",
                    "title": "Verify the Request",
                    "inject": "The email asks for urgency, secrecy, and an unusual payment method. The CEO is listed as 'in meetings'.",
                    "choices": [
                        {"id": "c1a", "text": "Call the CEO directly on their known mobile number to verify before taking any action", "score": 1.0, "feedback": "Out-of-band verification is the gold standard for BEC. Never rely solely on email for financial authorisations.", "consequence": "CEO confirms no such request was made. Attack averted. £47k saved."},
                        {"id": "c1b", "text": "Reply to the email asking for more details about the acquisition", "score": 0.0, "feedback": "Replying to the attacker's email confirms your address is active and may accelerate the scam.", "consequence": "Attacker sends more convincing documentation and increased pressure."},
                        {"id": "c1c", "text": "Forward the email to IT security before taking any action", "score": 0.7, "feedback": "Good escalation — but calling the CEO first is faster and directly resolves the issue without delay.", "consequence": "IT confirms suspicious domain. Transfer blocked after 45-minute delay."},
                    ]
                },
                {
                    "phase_id": "p2",
                    "title": "Post-Incident Actions",
                    "inject": "You've confirmed it's a BEC attempt. No money has been transferred. What do you do next?",
                    "choices": [
                        {"id": "c2a", "text": "Report to Action Fraud, brief the CEO and board, and review payment controls policy", "score": 1.0, "feedback": "All three actions are correct: statutory reporting, internal awareness, and control review.", "consequence": "Incident logged. Board briefed. Dual-authorisation control added for wire transfers over £10k."},
                        {"id": "c2b", "text": "Delete the email and move on — no harm was done", "score": 0.0, "feedback": "Serious error. Near-miss incidents must be logged. The attack pattern should be shared to protect others.", "consequence": "Attacker tries again next month targeting a colleague. No awareness training done."},
                        {"id": "c2c", "text": "Just change your email password and warn your team informally", "score": 0.3, "feedback": "Awareness is good but insufficient. Formal reporting and control changes are required.", "consequence": "Informal warning sent. No formal incident record. Auditors later flag missing incident log."},
                    ]
                },
            ],
            "timed_challenges": [
                {
                    "challenge_id": "tc1",
                    "task": "What term describes verifying a request through a different communication channel than the one used to make the request?",
                    "time_limit_seconds": 30,
                    "hints": ["'Out of ___' verification"],
                    "answer_key": "out of band verification",
                    "explanation": "Out-of-band (OOB) verification means using a different channel (e.g., phone call) to confirm a request received via email, preventing BEC and spoofed communications."
                },
                {
                    "challenge_id": "tc2",
                    "task": "What UK organisation should you report a fraud or BEC attempt to?",
                    "time_limit_seconds": 30,
                    "hints": ["National reporting centre for fraud"],
                    "answer_key": "action fraud",
                    "explanation": "Action Fraud is the UK's national reporting centre for fraud and cybercrime. Reports feed into the National Fraud Intelligence Bureau (NFIB)."
                },
            ],
        },
        {
            "title": "Insider Threat: The Departing Developer",
            "category": ScenarioCategory.INSIDER_THREAT,
            "difficulty": DifficultyLevel.ADVANCED,
            "synopsis": "A senior developer gives notice. During their final week, DLP alerts flag large data exports to a personal cloud account. HR wants to handle it quietly. IT and legal disagree.",
            "context": {"sector": "Technology", "employees": 120, "role": "Security Manager"},
            "initial_inject": "Your DLP system alerts at 23:11 on a Wednesday: a developer who gave notice last Friday has transferred 14GB to their personal Dropbox over the past three days, including source code repositories and client data. They're due to finish on Friday. HR says 'Let's not make a scene.' What do you do right now?",
            "estimated_minutes": 40,
            "frameworks": ["ISO 27001 A.7.3", "UK GDPR", "NCSC Insider Threat"],
            "learning_objectives": ["Balance legal rights with security response", "Understand data exfiltration evidence preservation", "Apply proportionate access revocation", "Navigate HR and legal intersection"],
            "phases": [
                {
                    "phase_id": "p1",
                    "title": "Immediate Containment",
                    "inject": "It's 23:11. The developer is not currently logged in. The transfer appears complete.",
                    "choices": [
                        {"id": "c1a", "text": "Preserve forensic evidence of the transfer, suspend cloud sync access, but do not revoke all access yet without legal sign-off", "score": 1.0, "feedback": "Proportionate and legally sound. Evidence preservation is critical. Full access revocation without legal consultation risks employment law exposure.", "consequence": "Evidence preserved. Legal and HR briefed first thing. Proportionate response maintained."},
                        {"id": "c1b", "text": "Immediately revoke all access and call the police", "score": 0.4, "feedback": "Revoking access overnight without HR/legal involvement may breach employment contract terms. Police involvement is appropriate but should follow legal guidance.", "consequence": "Employment lawyer flags potential unfair dismissal risk. Evidence still intact."},
                        {"id": "c1c", "text": "Do nothing until business hours — it's late and HR said not to make a scene", "score": 0.0, "feedback": "Inaction when evidence of data exfiltration is live is unacceptable. The developer could complete additional transfers overnight.", "consequence": "Another 4GB transferred overnight. Evidence of intent strengthens but data loss increases."},
                    ]
                },
                {
                    "phase_id": "p2",
                    "title": "Legal and HR Navigation",
                    "inject": "Legal confirms the developer has likely breached their employment contract and possibly the Computer Misuse Act. HR still wants to handle it as a quiet 'mutual agreement' to avoid publicity.",
                    "choices": [
                        {"id": "c2a", "text": "Override HR's preference — the Computer Misuse Act breach and potential UK GDPR violation require formal incident response", "score": 1.0, "feedback": "Correct. UK GDPR breach obligations and CMA criminal exposure mean a quiet exit is legally untenable.", "consequence": "Formal investigation proceeds. Solicitors engaged. ICO notified of potential breach involving client PII."},
                        {"id": "c2b", "text": "Agree with HR — offer a settlement, require deletion confirmation, and monitor externally", "score": 0.35, "feedback": "Settlement doesn't meet GDPR breach notification obligations if client PII was exfiltrated. This approach risks regulatory action.", "consequence": "Developer signs deletion confirmation. ICO later finds no notification was filed. Investigation opens."},
                        {"id": "c2c", "text": "Refer everything to legal and step back — it's no longer a security issue", "score": 0.3, "feedback": "Security's role continues: evidence preservation, scope assessment, and breach notification support are all still required.", "consequence": "Legal takes over but lacks technical context. Evidence handling delayed."},
                    ]
                },
            ],
            "timed_challenges": [
                {
                    "challenge_id": "tc1",
                    "task": "Name the UK legislation that makes unauthorised access to computer systems a criminal offence.",
                    "time_limit_seconds": 30,
                    "hints": ["Passed in 1990, updated since"],
                    "answer_key": "computer misuse act",
                    "explanation": "The Computer Misuse Act 1990 (CMA) criminalises unauthorised access to computer systems and data, unauthorised modification, and related offences."
                },
                {
                    "challenge_id": "tc2",
                    "task": "Under UK GDPR, what type of breach triggers a mandatory report to the ICO?",
                    "time_limit_seconds": 45,
                    "hints": ["Risk to individuals' rights and freedoms"],
                    "answer_key": "personal data breach likely to result in risk to individuals",
                    "explanation": "UK GDPR Art.33 requires reporting when a personal data breach is 'likely to result in a risk to the rights and freedoms of natural persons.' Exfiltration of client PII meets this threshold."
                },
            ],
        }
    ]

    for s_data in scenarios:
        s = IncidentScenario(**s_data)
        db.add(s)

    db.commit()
    return {"message": f"Seeded {len(scenarios)} scenarios"}
