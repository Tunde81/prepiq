from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from datetime import datetime
import openai
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User, UserProgress, LearningModule, RiskAssessment, Organisation

router = APIRouter()

FRAMEWORKS = {
    "cyber_essentials": {"name": "Cyber Essentials", "modules": ["phishing-awareness","password-security","device-security","safe-browsing","network-security-basics","email-security-and-anti-phishing","mobile-device-security-essentials","understanding-vulnerability-management"]},
    "gdpr": {"name": "UK GDPR", "modules": ["understanding-data-protection-and-gdpr","data-handling-gdpr","understanding-identity-and-access-management","cloud-security-best-practices","secure-software-development-practices"]},
    "dora": {"name": "DORA", "modules": ["understanding-dora-compliance-for-financial-services","incident-response-planning-essentials","business-continuity-and-disaster-recovery-essentials","understanding-vulnerability-management","understanding-supply-chain-security","introduction-to-threat-hunting-techniques","dark-web-monitoring-and-threat-intelligence"]},
    "fca": {"name": "FCA Cyber Resilience", "modules": ["understanding-fca-cyber-resilience-requirements","understanding-dora-compliance-for-financial-services","incident-response-planning-essentials","business-continuity-and-disaster-recovery-essentials","understanding-identity-and-access-management","introduction-to-security-operations-centre"]},
    "nis2": {"name": "NIS2 Directive", "modules": ["incident-response-planning-essentials","understanding-vulnerability-management","network-security-basics","understanding-supply-chain-security","business-continuity-and-disaster-recovery-essentials","cloud-security-best-practices","introduction-to-security-operations-centre","cryptography-essentials"]},
}

async def get_ai_recommendations(user_name, compliance_data, risk_score, progress_pct, org_name):
    if not settings.OPENAI_API_KEY:
        return ["Complete outstanding compliance modules", "Conduct a full cyber risk assessment", "Implement regular security awareness training"]
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    prompt = f"""You are a UK cybersecurity advisor writing board-level recommendations for {org_name or user_name}.
Current status:
- Training Progress: {progress_pct}%
- Risk Score: {risk_score or "Not assessed"}
- Compliance: {json.dumps({k: v["percent"] for k, v in compliance_data.items()})}

Write exactly 4 concise, actionable board-level recommendations. Return ONLY a JSON array of 4 strings. UK English. Each under 20 words."""
    try:
        r = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "Return only valid JSON array of 4 strings."}, {"role": "user", "content": prompt}],
            max_tokens=300, temperature=0.7
        )
        return json.loads(r.choices[0].message.content)
    except:
        return ["Complete outstanding compliance training modules as a priority.", "Conduct a comprehensive cyber risk assessment.", "Implement multi-factor authentication across all systems.", "Establish an incident response plan and test it quarterly."]


def build_pdf(data: dict) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

    buf = BytesIO()
    w, h = A4

    BG = colors.HexColor("#0a0e1a")
    ACCENT = colors.HexColor("#00d4ff")
    WHITE = colors.HexColor("#e2e8f0")
    MUTED = colors.HexColor("#6b7280")
    GREEN = colors.HexColor("#22c55e")
    YELLOW = colors.HexColor("#eab308")
    RED = colors.HexColor("#ef4444")
    SURFACE = colors.HexColor("#0d1626")
    BORDER = colors.HexColor("#1e3a5f")

    c = canvas.Canvas(buf, pagesize=A4)

    def draw_page_bg():
        c.setFillColor(BG)
        c.rect(0, 0, w, h, fill=1, stroke=0)
        c.setFillColor(ACCENT)
        c.rect(0, h - 2*mm, w, 2*mm, fill=1, stroke=0)
        c.setFillColor(BORDER)
        c.rect(0, 0, w, 0.5*mm, fill=1, stroke=0)

    def score_colour(s):
        if s is None: return MUTED
        if s >= 70: return GREEN
        if s >= 40: return YELLOW
        return RED

    # PAGE 1
    draw_page_bg()

    # Header
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(20*mm, h - 25*mm, "PREPIQ")
    c.setFont("Helvetica", 9)
    c.setFillColor(MUTED)
    c.drawString(20*mm, h - 32*mm, "UK National Cyber Preparedness Learning Platform")

    # Report title
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(20*mm, h - 50*mm, "Cyber Security Board Report")
    c.setFont("Helvetica", 11)
    c.setFillColor(MUTED)
    c.drawString(20*mm, h - 58*mm, f"Prepared for: {data['org_name']}")
    c.drawString(20*mm, h - 65*mm, f"Date: {data['date']}")
    c.drawString(20*mm, h - 72*mm, f"Prepared by: {data['user_name']}")

    # Divider
    c.setStrokeColor(BORDER)
    c.setLineWidth(1)
    c.line(20*mm, h - 78*mm, w - 20*mm, h - 78*mm)

    # Executive Summary
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(20*mm, h - 90*mm, "Executive Summary")

    c.setFillColor(WHITE)
    c.setFont("Helvetica", 10)
    summary_lines = data["executive_summary"].split(". ")
    y = h - 100*mm
    for line in summary_lines:
        if line.strip():
            c.drawString(20*mm, y, line.strip() + ("." if not line.endswith(".") else ""))
            y -= 6*mm

    # Key Metrics boxes
    y -= 5*mm
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(20*mm, y, "Key Metrics")
    y -= 10*mm

    metrics = [
        ("Training Progress", f"{data['progress_pct']}%", data['progress_pct']),
        ("Risk Score", str(data['risk_score']) if data['risk_score'] else "N/A", data['risk_score']),
        ("Overall Compliance", f"{data['overall_compliance']}%", data['overall_compliance']),
        ("Modules Completed", f"{data['modules_completed']}", min(100, data['modules_completed'] * 4)),
    ]

    box_w = (w - 40*mm) / 4
    for i, (label, value, score) in enumerate(metrics):
        x = 20*mm + i * box_w
        c.setFillColor(SURFACE)
        c.roundRect(x + 1*mm, y - 22*mm, box_w - 2*mm, 24*mm, 3*mm, fill=1, stroke=0)
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.5)
        c.roundRect(x + 1*mm, y - 22*mm, box_w - 2*mm, 24*mm, 3*mm, fill=0, stroke=1)
        sc = score if isinstance(score, (int, float)) and score is not None else 0
        c.setFillColor(score_colour(sc))
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(x + box_w/2, y - 10*mm, value)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        c.drawCentredString(x + box_w/2, y - 18*mm, label)

    y -= 32*mm

    # Compliance Table
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(20*mm, y, "Regulatory Compliance Status")
    y -= 8*mm

    for fw_id, fw in data["compliance"].items():
        pct = fw["percent"]
        col = score_colour(pct)
        status = "Compliant" if pct == 100 else "In Progress" if pct > 0 else "Not Started"

        c.setFillColor(SURFACE)
        c.roundRect(20*mm, y - 10*mm, w - 40*mm, 11*mm, 2*mm, fill=1, stroke=0)

        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(23*mm, y - 4*mm, fw["name"])

        c.setFillColor(col)
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(w - 22*mm, y - 2*mm, f"{pct}%")
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 7)
        c.drawRightString(w - 22*mm, y - 7*mm, status)

        bar_x = 55*mm
        bar_w = w - 90*mm
        c.setFillColor(BORDER)
        c.roundRect(bar_x, y - 5.5*mm, bar_w, 3*mm, 1*mm, fill=1, stroke=0)
        if pct > 0:
            c.setFillColor(col)
            c.roundRect(bar_x, y - 5.5*mm, bar_w * pct / 100, 3*mm, 1*mm, fill=1, stroke=0)

        y -= 13*mm

    # PAGE 2 - Recommendations
    c.showPage()
    draw_page_bg()

    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(20*mm, h - 25*mm, "Board Recommendations")

    y = h - 38*mm
    for i, rec in enumerate(data["recommendations"]):
        c.setFillColor(SURFACE)
        c.roundRect(20*mm, y - 14*mm, w - 40*mm, 16*mm, 3*mm, fill=1, stroke=0)
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1.5)
        c.line(20*mm, y - 14*mm, 20*mm, y + 2*mm)
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(24*mm, y - 3*mm, f"{i+1}.")
        c.setFillColor(WHITE)
        c.setFont("Helvetica", 10)
        c.drawString(30*mm, y - 3*mm, rec)
        y -= 20*mm

    # Footer
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawCentredString(w/2, 15*mm, f"PrepIQ Cyber Security Board Report — {data['date']} — prepiq.fa3tech.io — CONFIDENTIAL")

    c.save()
    return buf.getvalue()


@router.get("/generate")
async def generate_board_report(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Get progress
    total_modules = db.query(LearningModule).filter(LearningModule.is_published == True).count()
    completed = db.query(UserProgress).filter(UserProgress.user_id == current_user.id, UserProgress.status == "completed").count()
    progress_pct = round((completed / total_modules) * 100) if total_modules > 0 else 0

    # Get risk score
    assessment = db.query(RiskAssessment).filter(RiskAssessment.user_id == current_user.id).order_by(RiskAssessment.created_at.desc()).first()
    risk_score = assessment.overall_score if assessment else None

    # Get org
    org = db.query(Organisation).filter(Organisation.id == current_user.organisation_id).first() if current_user.organisation_id else None
    org_name = org.name if org else (current_user.full_name or current_user.email)

    # Get compliance
    all_modules = db.query(LearningModule).all()
    slug_to_id = {m.slug: m.id for m in all_modules}
    completed_ids = {p.module_id for p in db.query(UserProgress).filter(UserProgress.user_id == current_user.id, UserProgress.status == "completed").all()}

    compliance = {}
    for fw_id, fw in FRAMEWORKS.items():
        done = sum(1 for s in fw["modules"] if slug_to_id.get(s) in completed_ids)
        total = len(fw["modules"])
        compliance[fw_id] = {"name": fw["name"], "percent": round((done/total)*100) if total else 0}

    overall_compliance = round(sum(v["percent"] for v in compliance.values()) / len(compliance))

    # Executive summary
    risk_label = "Not yet assessed"
    if risk_score:
        risk_label = "Advanced" if risk_score >= 80 else "High" if risk_score >= 60 else "Medium" if risk_score >= 40 else "Low"

    summary = f"{org_name} has completed {progress_pct}% of available cybersecurity training modules. The current risk maturity level is {risk_label}. Overall regulatory compliance stands at {overall_compliance}% across five key frameworks. Immediate action is recommended to address compliance gaps and strengthen cyber resilience."

    # AI recommendations
    recommendations = await get_ai_recommendations(current_user.full_name or current_user.email, compliance, risk_score, progress_pct, org_name)

    pdf_data = {
        "org_name": org_name,
        "user_name": current_user.full_name or current_user.email,
        "date": datetime.now().strftime("%d %B %Y"),
        "progress_pct": progress_pct,
        "risk_score": risk_score,
        "overall_compliance": overall_compliance,
        "modules_completed": completed,
        "compliance": compliance,
        "executive_summary": summary,
        "recommendations": recommendations,
    }

    pdf_bytes = build_pdf(pdf_data)
    filename = f"PrepIQ_Board_Report_{datetime.now().strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
