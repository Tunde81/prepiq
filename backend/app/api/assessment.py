from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import os

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, AssessmentDomain, AssessmentQuestion, RiskAssessment
from app.services.report_generator import generate_pdf_report
from app.services.event_service import EventService

router = APIRouter()

# ─── SCORING ENGINE ───────────────────────────────────────────────────────────

MATURITY_LEVELS = [
    (0, 25, "critical", "Critical Risk"),
    (25, 45, "low", "Low Maturity"),
    (45, 65, "medium", "Developing"),
    (65, 80, "high", "Managed"),
    (80, 101, "advanced", "Advanced"),
]

REMEDIATION_TEMPLATES = {
    "Network Security": "Implement network segmentation, deploy NGFW, and conduct quarterly vulnerability scans.",
    "Identity & Access": "Enforce MFA across all accounts, implement PAM, and conduct quarterly access reviews.",
    "Data Protection": "Classify all data assets, encrypt sensitive data at rest and in transit, implement DLP.",
    "Incident Response": "Develop and test an IR plan quarterly, establish a SIRT, and implement SIEM.",
    "Endpoint Security": "Deploy EDR/XDR, enforce full-disk encryption, and implement application whitelisting.",
    "Security Awareness": "Run monthly phishing simulations and mandatory annual security awareness training.",
    "Vulnerability Management": "Establish a patch management programme and conduct quarterly penetration tests.",
    "Third-Party Risk": "Implement vendor risk assessments, review supplier contracts for security clauses.",
}


def calculate_scores(answers: dict, questions: list, domains: list) -> dict:
    domain_scores = {}
    for domain in domains:
        domain_q_ids = [q.id for q in domain.questions]
        domain_answers = [answers.get(str(qid), 0) for qid in domain_q_ids]
        if domain_answers:
            max_possible = len(domain_answers) * 3
            score = (sum(domain_answers) / max_possible) * 100
            domain_scores[str(domain.id)] = {
                "name": domain.name,
                "score": round(score, 1),
                "raw": sum(domain_answers),
                "max": max_possible,
            }
    return domain_scores


def get_maturity_level(score: float) -> tuple:
    for low, high, code, label in MATURITY_LEVELS:
        if low <= score < high:
            return code, label
    return "critical", "Critical Risk"


def identify_top_risks(domain_scores: dict) -> list:
    sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1]["score"])
    risks = []
    for domain_id, info in sorted_domains[:5]:
        score = info["score"]
        severity = "Critical" if score < 25 else "High" if score < 50 else "Medium"
        risks.append({
            "domain": info["name"],
            "score": score,
            "severity": severity,
            "recommendation": REMEDIATION_TEMPLATES.get(info["name"], "Review and improve controls in this domain."),
        })
    return risks


# ─── ROUTES ───────────────────────────────────────────────────────────────────

@router.get("/domains")
async def get_domains(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    domains = db.query(AssessmentDomain).order_by(AssessmentDomain.order_index).all()
    result = []
    for d in domains:
        questions = db.query(AssessmentQuestion).filter(
            AssessmentQuestion.domain_id == d.id
        ).order_by(AssessmentQuestion.order_index).all()
        result.append({
            "id": d.id,
            "name": d.name,
            "description": d.description,
            "questions": [{
                "id": q.id,
                "text": q.question_text,
                "guidance": q.guidance,
            } for q in questions]
        })
    return result


class SubmitAssessmentRequest(BaseModel):
    organisation_name: str
    organisation_sector: str
    answers: dict  # {question_id: score 0-3}


@router.post("/submit")
async def submit_assessment(
    payload: SubmitAssessmentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    domains = db.query(AssessmentDomain).all()
    domain_scores = calculate_scores(payload.answers, [], domains)

    if domain_scores:
        overall = sum(v["score"] for v in domain_scores.values()) / len(domain_scores)
    else:
        overall = 0

    maturity_code, maturity_label = get_maturity_level(overall)
    top_risks = identify_top_risks(domain_scores)

    assessment = RiskAssessment(
        user_id=current_user.id,
        organisation_name=payload.organisation_name,
        organisation_sector=payload.organisation_sector,
        answers=payload.answers,
        domain_scores=domain_scores,
        overall_score=round(overall, 1),
        maturity_level=maturity_code,
        top_risks=top_risks,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    background_tasks.add_task(
        EventService.track_assessment_complete,
        user_id=current_user.id,
        assessment_id=assessment.id,
        overall_score=assessment.overall_score,
        maturity_level=maturity_code,
        sector=payload.organisation_sector,
    )

    return {
        "id": assessment.id,
        "overall_score": assessment.overall_score,
        "maturity_level": maturity_code,
        "maturity_label": maturity_label,
        "domain_scores": domain_scores,
        "top_risks": top_risks,
        "created_at": assessment.created_at,
    }


@router.get("/history")
async def get_assessment_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assessments = db.query(RiskAssessment).filter(
        RiskAssessment.user_id == current_user.id
    ).order_by(RiskAssessment.created_at.desc()).limit(10).all()

    return [{
        "id": a.id,
        "organisation_name": a.organisation_name,
        "overall_score": a.overall_score,
        "maturity_level": a.maturity_level,
        "created_at": a.created_at,
    } for a in assessments]


@router.get("/{assessment_id}")
async def get_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assessment = db.query(RiskAssessment).filter(
        RiskAssessment.id == assessment_id,
        RiskAssessment.user_id == current_user.id
    ).first()
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    _, maturity_label = get_maturity_level(assessment.overall_score)

    return {
        "id": assessment.id,
        "organisation_name": assessment.organisation_name,
        "organisation_sector": assessment.organisation_sector,
        "overall_score": assessment.overall_score,
        "maturity_level": assessment.maturity_level,
        "maturity_label": maturity_label,
        "domain_scores": assessment.domain_scores,
        "top_risks": assessment.top_risks,
        "created_at": assessment.created_at,
    }


@router.get("/{assessment_id}/report")
async def download_report(
    assessment_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    assessment = db.query(RiskAssessment).filter(
        RiskAssessment.id == assessment_id,
        RiskAssessment.user_id == current_user.id
    ).first()
    if not assessment:
        raise HTTPException(404, "Assessment not found")

    pdf_path = generate_pdf_report(assessment, current_user)

    background_tasks.add_task(
        EventService.track_report_download,
        user_id=current_user.id,
        assessment_id=assessment_id,
    )

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"prepiq-risk-report-{assessment_id}.pdf"
    )
