from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
from datetime import datetime

BRAND_DARK = colors.HexColor("#0a0e1a")
BRAND_ACCENT = colors.HexColor("#00d4ff")
BRAND_GREEN = colors.HexColor("#00ff88")
BRAND_RED = colors.HexColor("#ff4444")
BRAND_ORANGE = colors.HexColor("#ff8800")
BRAND_YELLOW = colors.HexColor("#ffd700")


def severity_color(score: float):
    if score < 25:
        return BRAND_RED
    elif score < 50:
        return BRAND_ORANGE
    elif score < 75:
        return BRAND_YELLOW
    return BRAND_GREEN


def generate_pdf_report(assessment, user) -> str:
    os.makedirs("media/reports", exist_ok=True)
    path = f"media/reports/risk_report_{assessment.id}.pdf"

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", fontSize=22, textColor=BRAND_ACCENT, spaceAfter=6, alignment=TA_CENTER)
    subtitle_style = ParagraphStyle("subtitle", fontSize=12, textColor=colors.grey, spaceAfter=12, alignment=TA_CENTER)
    heading_style = ParagraphStyle("heading", fontSize=14, textColor=BRAND_ACCENT, spaceBefore=14, spaceAfter=6)
    body_style = ParagraphStyle("body", fontSize=10, textColor=colors.black, spaceAfter=4, leading=14)
    risk_style = ParagraphStyle("risk", fontSize=9, textColor=colors.white, spaceAfter=2)

    story = []

    # Header
    story.append(Paragraph("PrepIQ", title_style))
    story.append(Paragraph("Cyber Risk Assessment Report", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1, color=BRAND_ACCENT))
    story.append(Spacer(1, 0.3 * cm))

    # Meta
    story.append(Paragraph(f"<b>Organisation:</b> {assessment.organisation_name}", body_style))
    story.append(Paragraph(f"<b>Sector:</b> {assessment.organisation_sector}", body_style))
    story.append(Paragraph(f"<b>Prepared For:</b> {user.full_name} ({user.email})", body_style))
    story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d %B %Y')}", body_style))
    story.append(Spacer(1, 0.5 * cm))

    # Overall Score
    story.append(Paragraph("Overall Cyber Maturity Score", heading_style))
    score = assessment.overall_score
    maturity = assessment.maturity_level.upper()

    score_data = [
        ["Overall Score", f"{score:.1f} / 100", maturity],
    ]
    score_table = Table(score_data, colWidths=[5 * cm, 5 * cm, 5 * cm])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_DARK),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("TEXTCOLOR", (1, 0), (1, 0), BRAND_ACCENT),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BRAND_DARK]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.5 * cm))

    # Domain Scores
    story.append(Paragraph("Domain Breakdown", heading_style))
    domain_data = [["Domain", "Score", "Status"]]
    for domain_id, info in assessment.domain_scores.items():
        s = info["score"]
        status = "Critical" if s < 25 else "Low" if s < 50 else "Developing" if s < 65 else "Managed" if s < 80 else "Advanced"
        domain_data.append([info["name"], f"{s:.1f}%", status])

    domain_table = Table(domain_data, colWidths=[8 * cm, 3 * cm, 4 * cm])
    domain_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
        ("TEXTCOLOR", (0, 0), (-1, 0), BRAND_ACCENT),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(domain_table)
    story.append(Spacer(1, 0.5 * cm))

    # Top Risks
    story.append(Paragraph("Priority Risks & Recommendations", heading_style))
    for i, risk in enumerate(assessment.top_risks or [], 1):
        story.append(Paragraph(
            f"<b>{i}. {risk['domain']}</b> — Severity: {risk['severity']} | Score: {risk['score']:.1f}%",
            body_style
        ))
        story.append(Paragraph(f"→ {risk['recommendation']}", body_style))
        story.append(Spacer(1, 0.2 * cm))

    # Footer
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Paragraph(
        "This report was generated by PrepIQ. It is for internal use only and does not constitute formal security certification.",
        ParagraphStyle("footer", fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(story)
    return path
