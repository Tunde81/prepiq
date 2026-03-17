"""
PrepIQ - UK SME Cyber Health Index Router
Endpoints: assessment CRUD, scoring engine, benchmarks, dashboard aggregates
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from .health_index_models import (
    HealthIndexQuestion, HealthIndexAssessment, HealthIndexResponse,
    HealthIndexBenchmark, HealthDomain, RiskTier, AssessmentStatus
)

router = APIRouter(prefix="/api/health-index", tags=["health-index"])

# Import PDF export endpoint
from app.features.health_index_pdf import export_pdf, build_health_index_pdf  # noqa
router.add_api_route(
    "/assessment/{assessment_id}/export-pdf",
    export_pdf,
    methods=["GET"],
    tags=["health-index"]
)


# ─────────────────────────────────────────────
# Pydantic schemas
# ─────────────────────────────────────────────

class AssessmentStartRequest(BaseModel):
    employee_count: str          # <10 | 10-49 | 50-249
    sector: str
    has_it_team: bool
    has_cyber_insurance: bool


class AnswerSubmit(BaseModel):
    question_id: int
    answer_value: str


class BulkAnswerSubmit(BaseModel):
    answers: List[AnswerSubmit]


# ─────────────────────────────────────────────
# Scoring engine
# ─────────────────────────────────────────────

LIKERT_SCORE_MAP = {
    "1": 0.0,   # Never / Not at all
    "2": 0.25,
    "3": 0.5,   # Sometimes / Partially
    "4": 0.75,
    "5": 1.0,   # Always / Fully implemented
}

BOOLEAN_SCORE_MAP = {
    "yes": 1.0,
    "no": 0.0,
    "partial": 0.5,
}

DOMAIN_WEIGHTS = {
    HealthDomain.GOVERNANCE: 0.12,
    HealthDomain.ASSET_MANAGEMENT: 0.08,
    HealthDomain.ACCESS_CONTROL: 0.14,
    HealthDomain.NETWORK_SECURITY: 0.12,
    HealthDomain.INCIDENT_RESPONSE: 0.10,
    HealthDomain.SUPPLY_CHAIN: 0.08,
    HealthDomain.STAFF_AWARENESS: 0.12,
    HealthDomain.DATA_PROTECTION: 0.12,
    HealthDomain.PATCHING: 0.08,
    HealthDomain.BACKUP_RECOVERY: 0.04,
}


def score_answer(question: HealthIndexQuestion, answer_value: str) -> float:
    v = answer_value.lower().strip()
    if question.answer_type == "boolean":
        return BOOLEAN_SCORE_MAP.get(v, 0.0) * question.weight
    elif question.answer_type == "likert5":
        return LIKERT_SCORE_MAP.get(v, 0.0) * question.weight
    elif question.answer_type == "multi_choice":
        if question.options:
            opts = question.options if isinstance(question.options, list) else []
            selected = [x.strip() for x in v.split(",")]
            positive = [o for o in opts if o.get("positive", False)]
            if positive:
                matched = sum(1 for p in positive if p["value"] in selected)
                return (matched / len(positive)) * question.weight
    return 0.0


def compute_domain_scores(responses: list, questions: dict) -> dict:
    """Returns {domain: normalised_score_0_to_100}"""
    domain_totals = {d: {"earned": 0.0, "max": 0.0} for d in HealthDomain}
    for r in responses:
        q = questions.get(r.question_id)
        if not q:
            continue
        domain_totals[q.domain]["earned"] += r.score_contribution or 0.0
        domain_totals[q.domain]["max"] += q.weight
    result = {}
    for d, vals in domain_totals.items():
        if vals["max"] > 0:
            result[d.value] = round((vals["earned"] / vals["max"]) * 100, 1)
        else:
            result[d.value] = None
    return result


def compute_overall_score(domain_scores: dict) -> float:
    total = 0.0
    for domain, weight in DOMAIN_WEIGHTS.items():
        score = domain_scores.get(domain.value)
        if score is not None:
            total += score * weight
    return round(total, 1)


def score_to_tier(score: float) -> RiskTier:
    if score >= 80:
        return RiskTier.SECURE
    elif score >= 65:
        return RiskTier.LOW
    elif score >= 45:
        return RiskTier.MEDIUM
    elif score >= 25:
        return RiskTier.HIGH
    else:
        return RiskTier.CRITICAL


def generate_recommendations(domain_scores: dict) -> list:
    """Returns top 5 prioritised actions based on lowest domain scores."""
    DOMAIN_ACTIONS = {
        "governance": {
            "title": "Establish a Cyber Security Policy",
            "detail": "Document acceptable use, incident response responsibilities, and data classification. Align with NCSC Cyber Essentials.",
            "effort": "medium", "impact": "high"
        },
        "access_control": {
            "title": "Enforce Multi-Factor Authentication",
            "detail": "Require MFA on all admin accounts, email, and cloud services. Start with Microsoft 365 / Google Workspace.",
            "effort": "low", "impact": "high"
        },
        "patching": {
            "title": "Implement a Patch Management Schedule",
            "detail": "Apply critical patches within 14 days. Use WSUS or a patch management tool. Automate where possible.",
            "effort": "low", "impact": "high"
        },
        "network_security": {
            "title": "Segment Your Network",
            "detail": "Separate guest Wi-Fi from corporate. Use firewall rules to restrict lateral movement. Review open ports monthly.",
            "effort": "medium", "impact": "high"
        },
        "staff_awareness": {
            "title": "Run Phishing Simulation Training",
            "detail": "Use a platform like KnowBe4 or PrepIQ's own modules. Quarterly simulations reduce click rates by up to 70%.",
            "effort": "low", "impact": "high"
        },
        "incident_response": {
            "title": "Write and Test an Incident Response Plan",
            "detail": "Document roles, escalation paths, and containment steps. Run a tabletop exercise annually.",
            "effort": "medium", "impact": "high"
        },
        "data_protection": {
            "title": "Map and Encrypt Sensitive Data",
            "detail": "Complete a data flow audit. Encrypt data at rest and in transit. Ensure ICO registration is current.",
            "effort": "medium", "impact": "high"
        },
        "backup_recovery": {
            "title": "Implement 3-2-1 Backup Strategy",
            "detail": "3 copies, 2 media types, 1 offsite. Test restoration monthly. Aim for sub-4-hour RTO.",
            "effort": "low", "impact": "critical"
        },
        "supply_chain": {
            "title": "Audit Third-Party Supplier Security",
            "detail": "Request Cyber Essentials certification from key suppliers. Review data processing agreements under UK GDPR.",
            "effort": "medium", "impact": "medium"
        },
        "asset_management": {
            "title": "Maintain a Full Asset Inventory",
            "detail": "Track all hardware, software, and cloud services. Use tools like Lansweeper or an IT asset management spreadsheet.",
            "effort": "low", "impact": "medium"
        },
    }
    scored_domains = [(d, s) for d, s in domain_scores.items() if s is not None]
    scored_domains.sort(key=lambda x: x[1])
    recs = []
    for domain, score in scored_domains[:5]:
        action = DOMAIN_ACTIONS.get(domain, {})
        if action:
            recs.append({
                "domain": domain,
                "score": score,
                "priority": len(recs) + 1,
                **action
            })
    return recs


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────

@router.get("/questions")
def get_questions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return all active questions grouped by domain."""
    questions = db.query(HealthIndexQuestion).filter(
        HealthIndexQuestion.is_active == True
    ).order_by(HealthIndexQuestion.domain, HealthIndexQuestion.order_index).all()

    grouped = {}
    for q in questions:
        domain = q.domain.value
        if domain not in grouped:
            grouped[domain] = []
        grouped[domain].append({
            "id": q.id,
            "domain": domain,
            "question_text": q.question_text,
            "help_text": q.help_text,
            "answer_type": q.answer_type,
            "options": q.options,
            "weight": q.weight,
            "ncsc_reference": q.ncsc_reference,
            "fca_reference": q.fca_reference,
            "order_index": q.order_index,
        })
    return {"domains": grouped, "total": len(questions)}


@router.post("/assessment/start")
def start_assessment(
    req: AssessmentStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initialise a new assessment session for the user's org."""
    # Check for incomplete assessment — allow only one active per org
    existing = db.query(HealthIndexAssessment).filter(
        and_(
            HealthIndexAssessment.org_id == current_user.organisation_id,
            HealthIndexAssessment.status == AssessmentStatus.IN_PROGRESS
        )
    ).first()
    if existing:
        return {"assessment_id": existing.id, "resumed": True}

    assessment = HealthIndexAssessment(
        org_id=current_user.organisation_id,
        user_id=current_user.id,
        employee_count=req.employee_count,
        sector=req.sector,
        has_it_team=req.has_it_team,
        has_cyber_insurance=req.has_cyber_insurance,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return {"assessment_id": assessment.id, "resumed": False}


@router.post("/assessment/{assessment_id}/answers")
def submit_answers(
    assessment_id: int,
    payload: BulkAnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Save answers for one or more questions (supports partial saves)."""
    assessment = db.query(HealthIndexAssessment).filter_by(id=assessment_id).first()
    if not assessment or assessment.org_id != current_user.organisation_id:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.status != AssessmentStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Assessment already completed")

    question_ids = [a.question_id for a in payload.answers]
    questions = {
        q.id: q for q in db.query(HealthIndexQuestion).filter(
            HealthIndexQuestion.id.in_(question_ids)
        ).all()
    }

    for answer in payload.answers:
        q = questions.get(answer.question_id)
        if not q:
            continue
        contribution = score_answer(q, answer.answer_value)
        # Upsert response
        existing_resp = db.query(HealthIndexResponse).filter_by(
            assessment_id=assessment_id, question_id=answer.question_id
        ).first()
        if existing_resp:
            existing_resp.answer_value = answer.answer_value
            existing_resp.score_contribution = contribution
        else:
            resp = HealthIndexResponse(
                assessment_id=assessment_id,
                question_id=answer.question_id,
                answer_value=answer.answer_value,
                score_contribution=contribution,
            )
            db.add(resp)

    db.commit()
    return {"saved": len(payload.answers)}


@router.post("/assessment/{assessment_id}/complete")
def complete_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Finalise the assessment: compute scores, tier, benchmarks, recommendations."""
    assessment = db.query(HealthIndexAssessment).filter_by(id=assessment_id).first()
    if not assessment or assessment.org_id != current_user.organisation_id:
        raise HTTPException(status_code=404, detail="Assessment not found")

    responses = db.query(HealthIndexResponse).filter_by(assessment_id=assessment_id).all()
    if not responses:
        raise HTTPException(status_code=400, detail="No responses to score")

    question_ids = [r.question_id for r in responses]
    questions = {q.id: q for q in db.query(HealthIndexQuestion).filter(
        HealthIndexQuestion.id.in_(question_ids)
    ).all()}

    domain_scores = compute_domain_scores(responses, questions)
    overall = compute_overall_score(domain_scores)
    tier = score_to_tier(overall)
    recommendations = generate_recommendations(domain_scores)

    # Naive benchmark percentile vs stored benchmark data
    benchmark = db.query(HealthIndexBenchmark).filter(
        and_(
            HealthIndexBenchmark.domain == None,
            HealthIndexBenchmark.sector == assessment.sector
        )
    ).order_by(HealthIndexBenchmark.updated_at.desc()).first()

    percentile = None
    if benchmark:
        if overall >= benchmark.p75_score:
            percentile = 75 + ((overall - benchmark.p75_score) /
                               max(100 - benchmark.p75_score, 1)) * 25
        elif overall >= benchmark.p50_score:
            percentile = 50 + ((overall - benchmark.p50_score) /
                               max(benchmark.p75_score - benchmark.p50_score, 1)) * 25
        elif overall >= benchmark.p25_score:
            percentile = 25 + ((overall - benchmark.p25_score) /
                               max(benchmark.p50_score - benchmark.p25_score, 1)) * 25
        else:
            percentile = (overall / max(benchmark.p25_score, 1)) * 25
        percentile = round(min(99, max(1, percentile)), 0)

    assessment.overall_score = overall
    assessment.risk_tier = tier
    assessment.domain_scores = domain_scores
    assessment.benchmark_percentile = percentile
    assessment.recommendations = recommendations
    assessment.status = AssessmentStatus.COMPLETED
    assessment.completed_at = datetime.utcnow()
    db.commit()

    return {
        "overall_score": overall,
        "risk_tier": tier.value,
        "domain_scores": domain_scores,
        "benchmark_percentile": percentile,
        "recommendations": recommendations,
        "completed_at": assessment.completed_at.isoformat(),
    }


@router.get("/assessment/{assessment_id}/result")
def get_result(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full results for a completed assessment."""
    assessment = db.query(HealthIndexAssessment).filter_by(id=assessment_id).first()
    if not assessment or assessment.org_id != current_user.organisation_id:
        raise HTTPException(status_code=404, detail="Not found")
    if assessment.status != AssessmentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Assessment not yet completed")

    return {
        "assessment_id": assessment.id,
        "overall_score": assessment.overall_score,
        "risk_tier": assessment.risk_tier.value if assessment.risk_tier else None,
        "domain_scores": assessment.domain_scores,
        "benchmark_percentile": assessment.benchmark_percentile,
        "recommendations": assessment.recommendations,
        "sector": assessment.sector,
        "employee_count": assessment.employee_count,
        "completed_at": assessment.completed_at.isoformat() if assessment.completed_at else None,
    }


@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aggregate dashboard: latest score, history trend, domain radar, benchmarks."""
    latest = db.query(HealthIndexAssessment).filter(
        and_(
            HealthIndexAssessment.org_id == current_user.organisation_id,
            HealthIndexAssessment.status == AssessmentStatus.COMPLETED
        )
    ).order_by(HealthIndexAssessment.completed_at.desc()).first()

    history = db.query(HealthIndexAssessment).filter(
        and_(
            HealthIndexAssessment.org_id == current_user.organisation_id,
            HealthIndexAssessment.status == AssessmentStatus.COMPLETED
        )
    ).order_by(HealthIndexAssessment.completed_at.asc()).all()

    history_data = [
        {
            "date": a.completed_at.strftime("%b %Y") if a.completed_at else None,
            "score": a.overall_score,
            "tier": a.risk_tier.value if a.risk_tier else None,
        }
        for a in history
    ]

    # Sector benchmarks for current sector
    sector = latest.sector if latest else None
    benchmarks = {}
    if sector:
        bench_rows = db.query(HealthIndexBenchmark).filter_by(sector=sector).all()
        for b in bench_rows:
            key = b.domain.value if b.domain else "overall"
            benchmarks[key] = {
                "p25": b.p25_score, "p50": b.p50_score,
                "p75": b.p75_score, "avg": b.avg_score
            }

    return {
        "latest": {
            "assessment_id": latest.id if latest else None,
            "overall_score": latest.overall_score if latest else None,
            "risk_tier": latest.risk_tier.value if latest and latest.risk_tier else None,
            "benchmark_percentile": latest.benchmark_percentile if latest else None,
            "domain_scores": latest.domain_scores if latest else {},
            "recommendations": latest.recommendations if latest else [],
            "completed_at": latest.completed_at.isoformat() if latest and latest.completed_at else None,
        },
        "history": history_data,
        "benchmarks": benchmarks,
    }


@router.get("/benchmarks")
def get_benchmarks(
    sector: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return benchmark comparison data, optionally filtered by sector."""
    query = db.query(HealthIndexBenchmark)
    if sector:
        query = query.filter_by(sector=sector)
    rows = query.order_by(HealthIndexBenchmark.updated_at.desc()).all()
    return [
        {
            "sector": r.sector,
            "employee_band": r.employee_band,
            "domain": r.domain.value if r.domain else "overall",
            "avg_score": r.avg_score,
            "p25": r.p25_score,
            "p50": r.p50_score,
            "p75": r.p75_score,
            "sample_size": r.sample_size,
            "period": r.period,
        }
        for r in rows
    ]


# ─────────────────────────────────────────────
# Admin: seed questions
# ─────────────────────────────────────────────

@router.post("/admin/seed-questions")
def seed_questions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Seed the default UK SME question bank. Admin only."""
    if current_user.role.value not in ["superadmin", "admin"]:
        raise HTTPException(status_code=403, detail="Admin only")

    existing = db.query(HealthIndexQuestion).count()
    if existing > 0:
        return {"message": f"Questions already seeded ({existing} found)"}

    questions = [
        # GOVERNANCE
        {"domain": HealthDomain.GOVERNANCE, "question_text": "Does your organisation have a written cyber security policy reviewed in the last 12 months?", "answer_type": "boolean", "weight": 1.2, "ncsc_reference": "Cyber Essentials: Scope", "order_index": 1},
        {"domain": HealthDomain.GOVERNANCE, "question_text": "How often does senior leadership receive a cyber security briefing?", "answer_type": "likert5", "weight": 1.0, "order_index": 2, "help_text": "1=Never, 5=Monthly or more often"},
        {"domain": HealthDomain.GOVERNANCE, "question_text": "Does your organisation conduct annual cyber risk assessments?", "answer_type": "boolean", "weight": 1.0, "order_index": 3},
        {"domain": HealthDomain.GOVERNANCE, "question_text": "Is there a named individual responsible for cyber security decisions?", "answer_type": "boolean", "weight": 1.1, "order_index": 4},

        # ACCESS CONTROL
        {"domain": HealthDomain.ACCESS_CONTROL, "question_text": "Is multi-factor authentication (MFA) enforced for all user accounts accessing company systems?", "answer_type": "likert5", "weight": 1.5, "ncsc_reference": "Cyber Essentials: User Access Control", "order_index": 1},
        {"domain": HealthDomain.ACCESS_CONTROL, "question_text": "Are admin/privileged accounts separate from standard user accounts?", "answer_type": "boolean", "weight": 1.3, "order_index": 2},
        {"domain": HealthDomain.ACCESS_CONTROL, "question_text": "How rigorously is the principle of least privilege applied?", "answer_type": "likert5", "weight": 1.0, "order_index": 3, "help_text": "1=Not at all, 5=Strictly enforced across all systems"},
        {"domain": HealthDomain.ACCESS_CONTROL, "question_text": "Are leavers' accounts disabled on or before their last working day?", "answer_type": "likert5", "weight": 1.2, "order_index": 4},

        # NETWORK SECURITY
        {"domain": HealthDomain.NETWORK_SECURITY, "question_text": "Is a firewall in place between the internet and your internal network?", "answer_type": "boolean", "weight": 1.3, "ncsc_reference": "Cyber Essentials: Firewalls", "order_index": 1},
        {"domain": HealthDomain.NETWORK_SECURITY, "question_text": "Is your guest Wi-Fi network separated from your corporate network?", "answer_type": "boolean", "weight": 1.0, "order_index": 2},
        {"domain": HealthDomain.NETWORK_SECURITY, "question_text": "How frequently are firewall rules reviewed and unnecessary ports closed?", "answer_type": "likert5", "weight": 1.0, "order_index": 3},
        {"domain": HealthDomain.NETWORK_SECURITY, "question_text": "Is network traffic monitored for anomalies or suspicious activity?", "answer_type": "likert5", "weight": 1.1, "order_index": 4},

        # PATCHING
        {"domain": HealthDomain.PATCHING, "question_text": "Are operating system security patches applied within 14 days of release?", "answer_type": "likert5", "weight": 1.4, "ncsc_reference": "Cyber Essentials: Patch Management", "order_index": 1},
        {"domain": HealthDomain.PATCHING, "question_text": "Is software that is no longer supported by the vendor removed from your environment?", "answer_type": "likert5", "weight": 1.2, "order_index": 2},
        {"domain": HealthDomain.PATCHING, "question_text": "Are third-party applications (browsers, plugins, office suites) kept up to date?", "answer_type": "likert5", "weight": 1.0, "order_index": 3},

        # STAFF AWARENESS
        {"domain": HealthDomain.STAFF_AWARENESS, "question_text": "How regularly do all staff receive cyber security awareness training?", "answer_type": "likert5", "weight": 1.2, "order_index": 1, "help_text": "1=Never, 5=Quarterly or more often"},
        {"domain": HealthDomain.STAFF_AWARENESS, "question_text": "Does your organisation run phishing simulations to test staff resilience?", "answer_type": "boolean", "weight": 1.1, "order_index": 2},
        {"domain": HealthDomain.STAFF_AWARENESS, "question_text": "Is there a clear, easy process for staff to report suspicious emails or incidents?", "answer_type": "boolean", "weight": 1.0, "order_index": 3},
        {"domain": HealthDomain.STAFF_AWARENESS, "question_text": "Are new employees required to complete security awareness training before accessing systems?", "answer_type": "boolean", "weight": 1.0, "order_index": 4},

        # INCIDENT RESPONSE
        {"domain": HealthDomain.INCIDENT_RESPONSE, "question_text": "Does your organisation have a documented incident response plan?", "answer_type": "boolean", "weight": 1.3, "order_index": 1},
        {"domain": HealthDomain.INCIDENT_RESPONSE, "question_text": "Has the incident response plan been tested (e.g. tabletop exercise) in the last 12 months?", "answer_type": "boolean", "weight": 1.1, "order_index": 2},
        {"domain": HealthDomain.INCIDENT_RESPONSE, "question_text": "Do you know your legal obligation to report breaches to the ICO within 72 hours?", "answer_type": "boolean", "weight": 1.0, "fca_reference": "UK GDPR Art.33", "order_index": 3},
        {"domain": HealthDomain.INCIDENT_RESPONSE, "question_text": "Is there a retained relationship with an external incident response provider?", "answer_type": "boolean", "weight": 0.9, "order_index": 4},

        # DATA PROTECTION
        {"domain": HealthDomain.DATA_PROTECTION, "question_text": "Is sensitive data encrypted both at rest and in transit?", "answer_type": "likert5", "weight": 1.3, "fca_reference": "UK GDPR Art.32", "order_index": 1},
        {"domain": HealthDomain.DATA_PROTECTION, "question_text": "Has a data flow mapping exercise been completed in the last 24 months?", "answer_type": "boolean", "weight": 1.0, "order_index": 2},
        {"domain": HealthDomain.DATA_PROTECTION, "question_text": "Is your organisation registered with the ICO (where required)?", "answer_type": "boolean", "weight": 1.1, "order_index": 3},

        # BACKUP & RECOVERY
        {"domain": HealthDomain.BACKUP_RECOVERY, "question_text": "Does your backup strategy follow the 3-2-1 rule (3 copies, 2 media types, 1 offsite)?", "answer_type": "boolean", "weight": 1.3, "order_index": 1},
        {"domain": HealthDomain.BACKUP_RECOVERY, "question_text": "How often are backups tested for restorability?", "answer_type": "likert5", "weight": 1.2, "order_index": 2, "help_text": "1=Never, 5=Monthly"},
        {"domain": HealthDomain.BACKUP_RECOVERY, "question_text": "Are backups stored in a location isolated from your primary systems (e.g. air-gapped or immutable)?", "answer_type": "boolean", "weight": 1.1, "order_index": 3},

        # SUPPLY CHAIN
        {"domain": HealthDomain.SUPPLY_CHAIN, "question_text": "Do you assess the cyber security posture of key suppliers before engagement?", "answer_type": "likert5", "weight": 1.0, "order_index": 1},
        {"domain": HealthDomain.SUPPLY_CHAIN, "question_text": "Are data processing agreements (DPAs) in place with all suppliers who process personal data?", "answer_type": "boolean", "weight": 1.1, "fca_reference": "UK GDPR Art.28", "order_index": 2},
        {"domain": HealthDomain.SUPPLY_CHAIN, "question_text": "Do critical suppliers hold Cyber Essentials or equivalent certification?", "answer_type": "boolean", "weight": 1.0, "order_index": 3},

        # ASSET MANAGEMENT
        {"domain": HealthDomain.ASSET_MANAGEMENT, "question_text": "Is there an up-to-date inventory of all hardware assets (laptops, servers, mobile devices)?", "answer_type": "boolean", "weight": 1.0, "order_index": 1},
        {"domain": HealthDomain.ASSET_MANAGEMENT, "question_text": "Is there an up-to-date inventory of all software and cloud services in use?", "answer_type": "boolean", "weight": 1.0, "order_index": 2},
        {"domain": HealthDomain.ASSET_MANAGEMENT, "question_text": "Are shadow IT / unauthorised devices or applications actively detected and managed?", "answer_type": "likert5", "weight": 0.9, "order_index": 3},
    ]

    for q_data in questions:
        q = HealthIndexQuestion(**q_data)
        db.add(q)

    db.commit()
    return {"message": f"Seeded {len(questions)} questions across all domains"}


@router.post("/admin/seed-benchmarks")
def seed_benchmarks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Seed representative UK SME benchmark data. Admin only."""
    if current_user.role.value not in ["superadmin", "admin"]:
        raise HTTPException(status_code=403, detail="Admin only")

    existing = db.query(HealthIndexBenchmark).count()
    if existing > 0:
        return {"message": "Benchmarks already seeded"}

    # Representative UK SME benchmarks (based on NCSC/DSIT survey data patterns)
    sectors = ["Financial Services", "Professional Services", "Retail", "Healthcare",
               "Technology", "Education", "Manufacturing", "Charity/NGO"]
    benchmark_data = [
        # (sector, avg, p25, p50, p75, sample_size)
        ("Financial Services", 62, 48, 63, 76, 312),
        ("Professional Services", 55, 40, 56, 70, 489),
        ("Retail", 41, 28, 41, 55, 278),
        ("Healthcare", 48, 33, 49, 64, 201),
        ("Technology", 67, 53, 68, 80, 367),
        ("Education", 44, 30, 44, 59, 156),
        ("Manufacturing", 38, 24, 38, 52, 203),
        ("Charity/NGO", 35, 21, 35, 49, 144),
    ]

    for sector, avg, p25, p50, p75, n in benchmark_data:
        b = HealthIndexBenchmark(
            sector=sector,
            domain=None,
            avg_score=avg,
            p25_score=p25,
            p50_score=p50,
            p75_score=p75,
            sample_size=n,
            period="2025-Q1"
        )
        db.add(b)

    db.commit()
    return {"message": f"Seeded benchmarks for {len(benchmark_data)} sectors"}
