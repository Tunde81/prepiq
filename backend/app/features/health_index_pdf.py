"""
PrepIQ - UK SME Cyber Health Index PDF Report Generator
Appended to health_index_router.py as a new endpoint
"""

from fastapi import Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.features.health_index_models import HealthIndexAssessment, AssessmentStatus


def build_health_index_pdf(assessment, user) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas

    buf = BytesIO()
    w, h = A4

    # ── Colour palette (matches board_report.py) ──────────────────────────────
    BG      = colors.HexColor("#0a0e1a")
    ACCENT  = colors.HexColor("#00d4ff")
    WHITE   = colors.HexColor("#e2e8f0")
    MUTED   = colors.HexColor("#6b7280")
    GREEN   = colors.HexColor("#22c55e")
    YELLOW  = colors.HexColor("#eab308")
    RED     = colors.HexColor("#ef4444")
    ORANGE  = colors.HexColor("#f97316")
    SURFACE = colors.HexColor("#0d1626")
    BORDER  = colors.HexColor("#1e3a5f")
    INDIGO  = colors.HexColor("#6366f1")

    TIER_COLORS = {
        "secure":   colors.HexColor("#10b981"),
        "low":      colors.HexColor("#34d399"),
        "medium":   colors.HexColor("#fbbf24"),
        "high":     colors.HexColor("#f97316"),
        "critical": colors.HexColor("#ef4444"),
    }
    TIER_LABELS = {
        "secure": "Secure", "low": "Low Risk",
        "medium": "Medium Risk", "high": "High Risk", "critical": "Critical"
    }
    DOMAIN_LABELS = {
        "governance": "Governance", "asset_management": "Asset Management",
        "access_control": "Access Control", "network_security": "Network Security",
        "incident_response": "Incident Response", "supply_chain": "Supply Chain",
        "staff_awareness": "Staff Awareness", "data_protection": "Data Protection",
        "patching": "Patching", "backup_recovery": "Backup & Recovery",
    }

    def score_colour(s):
        if s is None: return MUTED
        if s >= 65: return GREEN
        if s >= 40: return YELLOW
        return RED

    def tier_colour(t):
        return TIER_COLORS.get(t, MUTED)

    def draw_page_bg(c):
        c.setFillColor(BG)
        c.rect(0, 0, w, h, fill=1, stroke=0)
        c.setFillColor(ACCENT)
        c.rect(0, h - 2*mm, w, 2*mm, fill=1, stroke=0)
        c.setFillColor(BORDER)
        c.rect(0, 0, w, 0.5*mm, fill=1, stroke=0)

    def draw_score_ring(c, cx, cy, radius, score, tier):
        import math
        score = score or 0
        tc = tier_colour(tier)
        # Background ring
        c.setStrokeColor(colors.HexColor("#1e3a5f"))
        c.setLineWidth(8)
        c.circle(cx, cy, radius, fill=0, stroke=1)
        # Score arc (approximated with bezier segments)
        c.setStrokeColor(tc)
        c.setLineWidth(8)
        angle = (score / 100) * 360
        steps = max(1, int(angle / 10))
        for i in range(steps):
            a1 = math.radians(90 - (i / steps) * angle)
            a2 = math.radians(90 - ((i + 1) / steps) * angle)
            x1 = cx + radius * math.cos(a1)
            y1 = cy + radius * math.sin(a1)
            x2 = cx + radius * math.cos(a2)
            y2 = cy + radius * math.sin(a2)
            c.line(x1, y1, x2, y2)
        # Score text
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 28)
        score_text = str(int(score))
        c.drawCentredString(cx, cy + 4*mm, score_text)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 9)
        c.drawCentredString(cx, cy - 4*mm, "/ 100")

    def draw_domain_bar(c, x, y, label, score, bar_width=120*mm):
        sc = score_colour(score)
        # Label
        c.setFillColor(WHITE)
        c.setFont("Helvetica", 9)
        c.drawString(x, y, label)
        # Score value
        c.setFillColor(sc)
        c.setFont("Helvetica-Bold", 9)
        score_str = f"{int(score)}" if score is not None else "N/A"
        c.drawRightString(x + bar_width + 12*mm, y, score_str)
        # Bar background
        bar_y = y - 4*mm
        c.setFillColor(BORDER)
        c.roundRect(x, bar_y, bar_width, 3*mm, 1*mm, fill=1, stroke=0)
        # Bar fill
        if score:
            fill_w = (score / 100) * bar_width
            c.setFillColor(sc)
            c.roundRect(x, bar_y, fill_w, 3*mm, 1*mm, fill=1, stroke=0)

    def draw_section_header(c, y, title):
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(20*mm, y, title)
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.5)
        c.line(20*mm, y - 3*mm, w - 20*mm, y - 3*mm)
        return y - 10*mm

    def draw_footer(c, page_num):
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        c.drawString(20*mm, 10*mm, "PrepIQ · UK National Cyber Preparedness Learning Platform · prepiq.fa3tech.io")
        c.drawRightString(w - 20*mm, 10*mm, f"Page {page_num} · CONFIDENTIAL")
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.5)
        c.line(20*mm, 14*mm, w - 20*mm, 14*mm)

    # ── Data extraction ───────────────────────────────────────────────────────
    overall     = assessment.overall_score or 0
    tier        = assessment.risk_tier.value if assessment.risk_tier else "medium"
    tier_label  = TIER_LABELS.get(tier, "Medium Risk")
    tier_col    = tier_colour(tier)
    domain_scores = assessment.domain_scores or {}
    recommendations = assessment.recommendations or []
    sector      = assessment.sector or "Not specified"
    emp_count   = assessment.employee_count or "Not specified"
    percentile  = assessment.benchmark_percentile
    completed   = assessment.completed_at.strftime("%d %B %Y") if assessment.completed_at else datetime.now().strftime("%d %B %Y")
    user_name   = user.full_name or user.email

    c = canvas.Canvas(buf, pagesize=A4)

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 1 — Cover + Executive Summary
    # ══════════════════════════════════════════════════════════════════════════
    draw_page_bg(c)

    # PrepIQ branding
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(20*mm, h - 25*mm, "PREPIQ")
    c.setFont("Helvetica", 9)
    c.setFillColor(MUTED)
    c.drawString(20*mm, h - 32*mm, "UK National Cyber Preparedness Learning Platform")

    # Flag + title block
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(20*mm, h - 52*mm, "UK SME Cyber Health Index")
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(ACCENT)
    c.drawString(20*mm, h - 62*mm, "Assessment Report")

    # Meta info
    c.setFont("Helvetica", 10)
    c.setFillColor(MUTED)
    c.drawString(20*mm, h - 74*mm, f"Prepared for:  {user_name}")
    c.drawString(20*mm, h - 81*mm, f"Sector:        {sector}")
    c.drawString(20*mm, h - 88*mm, f"Organisation:  {emp_count} employees")
    c.drawString(20*mm, h - 95*mm, f"Date:          {completed}")
    c.drawString(20*mm, h - 102*mm, f"Assessment ID: #{assessment.id}")

    # Divider
    c.setStrokeColor(BORDER)
    c.setLineWidth(1)
    c.line(20*mm, h - 108*mm, w - 20*mm, h - 108*mm)

    # Score ring (right side of page)
    ring_cx = w - 45*mm
    ring_cy = h - 75*mm
    draw_score_ring(c, ring_cx, ring_cy, 25*mm, overall, tier)

    # Tier badge below ring
    c.setFillColor(tier_col)
    c.roundRect(ring_cx - 20*mm, ring_cy - 40*mm, 40*mm, 8*mm, 2*mm, fill=1, stroke=0)
    c.setFillColor(BG)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(ring_cx, ring_cy - 35*mm, tier_label.upper())

    # Benchmark percentile
    if percentile:
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        c.drawCentredString(ring_cx, ring_cy - 46*mm, f"Better than {int(percentile)}% of UK SMEs")

    # Executive summary section
    y = h - 120*mm
    y = draw_section_header(c, y, "Executive Summary")

    # Summary text
    summary_lines = [
        f"This report presents the results of a UK SME Cyber Health Index assessment completed on {completed}.",
        f"The assessment evaluated {user_name}'s organisation across 10 cybersecurity domains,",
        f"covering governance, technical controls, staff awareness, and regulatory compliance.",
        f"",
        f"Overall Health Score: {int(overall)}/100  —  Risk Tier: {tier_label}",
    ]
    if percentile:
        summary_lines.append(f"Sector Benchmarking: Better than {int(percentile)}% of UK SMEs in {sector}.")
    summary_lines += [
        f"",
        f"The assessment is aligned with the NCSC Cyber Essentials framework, UK GDPR obligations,",
        f"and FCA SYSC 13 operational resilience requirements. The priority recommendations",
        f"contained in this report should be reviewed by senior leadership and incorporated",
        f"into the organisation's cyber risk register and improvement roadmap.",
    ]

    c.setFont("Helvetica", 10)
    for line in summary_lines:
        if line == "":
            y -= 4*mm
            continue
        c.setFillColor(WHITE if "Overall" in line or "Sector" in line else MUTED)
        if "Overall" in line or "Sector" in line:
            c.setFont("Helvetica-Bold", 10)
        else:
            c.setFont("Helvetica", 10)
        c.drawString(20*mm, y, line)
        y -= 6*mm

    # KPI strip at bottom of page 1
    y -= 5*mm
    kpis = [
        ("Overall Score", f"{int(overall)}/100", score_colour(overall)),
        ("Risk Tier", tier_label, tier_col),
        ("Domains Assessed", "10", ACCENT),
        ("Sector", sector[:18], INDIGO),
    ]
    box_w = (w - 40*mm) / len(kpis)
    for i, (label, value, col) in enumerate(kpis):
        bx = 20*mm + i * box_w
        c.setFillColor(SURFACE)
        c.roundRect(bx, y - 18*mm, box_w - 3*mm, 18*mm, 2*mm, fill=1, stroke=0)
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.5)
        c.roundRect(bx, y - 18*mm, box_w - 3*mm, 18*mm, 2*mm, fill=0, stroke=1)
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 7)
        c.drawCentredString(bx + (box_w - 3*mm)/2, y - 6*mm, label.upper())
        c.setFillColor(col)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(bx + (box_w - 3*mm)/2, y - 14*mm, str(value))

    draw_footer(c, 1)
    c.showPage()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 2 — Domain Scores
    # ══════════════════════════════════════════════════════════════════════════
    draw_page_bg(c)

    y = h - 25*mm
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20*mm, y, "Domain Score Breakdown")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(20*mm, y - 7*mm, "Scores reflect maturity level across each cybersecurity domain. Benchmark median shown as reference line.")
    y -= 18*mm

    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.line(20*mm, y + 2*mm, w - 20*mm, y + 2*mm)

    bar_width = 115*mm
    for domain, score in domain_scores.items():
        label = DOMAIN_LABELS.get(domain, domain.replace("_", " ").title())
        if score is None:
            continue
        # Domain row background
        row_h = 14*mm
        c.setFillColor(SURFACE)
        c.roundRect(20*mm, y - row_h + 2*mm, w - 40*mm, row_h, 1*mm, fill=1, stroke=0)

        draw_domain_bar(c, 24*mm, y - 4*mm, label, score, bar_width)

        # Score interpretation
        interp = "Strong" if score >= 65 else "Needs Attention" if score >= 40 else "Critical Gap"
        ic = score_colour(score)
        c.setFillColor(ic)
        c.setFont("Helvetica", 7)
        c.drawRightString(w - 20*mm, y - 4*mm, interp)

        y -= row_h + 1*mm

    # Score legend
    y -= 5*mm
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(20*mm, y, "Score Guide:")
    for label, col, threshold in [("65-100 Strong", GREEN, None), ("40-64 Needs Attention", YELLOW, None), ("0-39 Critical Gap", RED, None)]:
        c.setFillColor(col)
        c.drawString(55*mm, y, "●")
        c.setFillColor(MUTED)
        c.drawString(60*mm, y, label)
        y_offset = 0

    draw_footer(c, 2)
    c.showPage()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 3 — Priority Recommendations
    # ══════════════════════════════════════════════════════════════════════════
    draw_page_bg(c)

    y = h - 25*mm
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20*mm, y, "Priority Recommendations")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 9)
    c.drawString(20*mm, y - 7*mm, "Actions ranked by domain score. Address Critical and High priority items first.")
    y -= 20*mm

    effort_colors = {"low": GREEN, "medium": YELLOW, "high": ORANGE}
    impact_colors = {"critical": INDIGO, "high": GREEN, "medium": YELLOW}

    for i, rec in enumerate(recommendations):
        domain_score = rec.get("score", 0)
        rc = score_colour(domain_score)
        rec_h = 28*mm

        # Card background
        c.setFillColor(SURFACE)
        c.roundRect(20*mm, y - rec_h, w - 40*mm, rec_h, 2*mm, fill=1, stroke=0)
        c.setStrokeColor(rc)
        c.setLineWidth(2)
        c.line(20*mm, y - rec_h, 20*mm, y)

        # Priority number
        c.setFillColor(rc)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(24*mm, y - 8*mm, f"#{i+1}")

        # Title
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(34*mm, y - 8*mm, rec.get("title", ""))

        # Domain score
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        domain_label = DOMAIN_LABELS.get(rec.get("domain",""), rec.get("domain","").replace("_"," ").title())
        c.drawRightString(w - 22*mm, y - 8*mm, f"{domain_label}: {int(domain_score)}/100")

        # Detail text (wrap at ~90 chars)
        detail = rec.get("detail", "")
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 9)
        if len(detail) > 90:
            mid = detail[:90].rfind(" ")
            c.drawString(34*mm, y - 15*mm, detail[:mid])
            c.drawString(34*mm, y - 20*mm, detail[mid+1:120] + ("..." if len(detail) > 120 else ""))
        else:
            c.drawString(34*mm, y - 15*mm, detail)

        # Effort + Impact badges
        effort = rec.get("effort", "medium")
        impact = rec.get("impact", "medium")
        ec = effort_colors.get(effort, YELLOW)
        ic = impact_colors.get(impact, GREEN)

        bx = 34*mm
        for badge_label, badge_col in [(f"Effort: {effort.title()}", ec), (f"Impact: {impact.title()}", ic)]:
            c.setFillColor(badge_col)
            c.roundRect(bx, y - rec_h + 3*mm, 28*mm, 5*mm, 1*mm, fill=1, stroke=0)
            c.setFillColor(BG)
            c.setFont("Helvetica-Bold", 7)
            c.drawCentredString(bx + 14*mm, y - rec_h + 5.5*mm, badge_label.upper())
            bx += 30*mm

        y -= rec_h + 2*mm

        if y < 40*mm and i < len(recommendations) - 1:
            draw_footer(c, 3)
            c.showPage()
            draw_page_bg(c)
            y = h - 25*mm

    draw_footer(c, 3)
    c.showPage()

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 4 — Compliance & Frameworks
    # ══════════════════════════════════════════════════════════════════════════
    draw_page_bg(c)

    y = h - 25*mm
    c.setFillColor(ACCENT)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20*mm, y, "Regulatory & Framework Alignment")
    y -= 15*mm

    frameworks = [
        {
            "name": "NCSC Cyber Essentials",
            "desc": "The UK Government-backed scheme defining five technical controls: firewalls, secure configuration, access control, malware protection, and patch management.",
            "relevance": "Directly mapped across Access Control, Network Security, and Patching domains.",
            "url": "https://www.ncsc.gov.uk/cyberessentials"
        },
        {
            "name": "UK GDPR & Data Protection Act 2018",
            "desc": "Requires organisations to implement appropriate technical and organisational measures to protect personal data (Art.32) and report breaches to the ICO within 72 hours (Art.33).",
            "relevance": "Mapped to Data Protection and Incident Response domains.",
            "url": "https://ico.org.uk"
        },
        {
            "name": "FCA SYSC 13 — Operational Risk",
            "desc": "FCA rules requiring firms to maintain robust IT and operational risk management, including business continuity and third-party risk management.",
            "relevance": "Relevant to Governance, Supply Chain, and Backup & Recovery domains.",
            "url": "https://www.handbook.fca.org.uk/handbook/SYSC/13/"
        },
        {
            "name": "NIST Cybersecurity Framework (CSF)",
            "desc": "Five core functions: Identify, Protect, Detect, Respond, Recover. Widely adopted globally as a risk management framework.",
            "relevance": "Underpins the scoring methodology across all 10 assessment domains.",
            "url": "https://www.nist.gov/cyberframework"
        },
    ]

    for fw in frameworks:
        fw_h = 28*mm
        c.setFillColor(SURFACE)
        c.roundRect(20*mm, y - fw_h, w - 40*mm, fw_h, 2*mm, fill=1, stroke=0)
        c.setStrokeColor(ACCENT)
        c.setLineWidth(1.5)
        c.line(20*mm, y - fw_h, 20*mm, y)

        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(26*mm, y - 7*mm, fw["name"])

        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8.5)
        desc = fw["desc"]
        if len(desc) > 95:
            mid = desc[:95].rfind(" ")
            c.drawString(26*mm, y - 13*mm, desc[:mid])
            c.drawString(26*mm, y - 18*mm, desc[mid+1:])
        else:
            c.drawString(26*mm, y - 13*mm, desc)

        c.setFillColor(GREEN)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(26*mm, y - 23*mm, "► " + fw["relevance"])

        y -= fw_h + 3*mm

    # Disclaimer
    y -= 5*mm
    c.setStrokeColor(BORDER)
    c.line(20*mm, y, w - 20*mm, y)
    y -= 8*mm
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7.5)
    disclaimer_lines = [
        "DISCLAIMER: This report is generated by PrepIQ for informational and educational purposes.",
        "It does not constitute professional legal, regulatory, or cybersecurity advice.",
        "Organisations should engage qualified cybersecurity professionals for formal risk assessments and compliance reviews.",
        f"Report generated: {datetime.now(timezone.utc).strftime('%d %B %Y at %H:%M UTC')} · Assessment ID: #{assessment.id}",
    ]
    for line in disclaimer_lines:
        c.drawString(20*mm, y, line)
        y -= 5*mm

    draw_footer(c, 4)
    c.save()
    return buf.getvalue()


def export_pdf(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export a completed Health Index assessment as a branded PDF report."""
    assessment = db.query(HealthIndexAssessment).filter_by(id=assessment_id).first()
    if not assessment or assessment.org_id != current_user.organisation_id:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.status != AssessmentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Assessment not yet completed")

    pdf_bytes = build_health_index_pdf(assessment, current_user)
    filename = f"PrepIQ_Health_Index_{assessment_id}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
