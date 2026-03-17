from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserProgress, LearningModule

router = APIRouter()

@router.get("/module/{module_id}")
async def generate_certificate(
    module_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    progress = db.query(UserProgress).filter(
        UserProgress.user_id == current_user.id,
        UserProgress.module_id == module_id,
        UserProgress.status == "completed"
    ).first()
    if not progress:
        raise HTTPException(403, "Module not completed yet")

    module = db.query(LearningModule).filter(LearningModule.id == module_id).first()
    if not module:
        raise HTTPException(404, "Module not found")

    pdf = generate_pdf_certificate(
        name=current_user.full_name or current_user.email,
        module_title=module.title,
        completed_at=progress.completed_at or datetime.utcnow(),
        certificate_id=f"PREPIQ-{current_user.id:04d}-{module_id:04d}"
    )

    return StreamingResponse(
        BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=PrepIQ_Certificate_{module.slug}.pdf"}
    )


def generate_pdf_certificate(name, module_title, completed_at, certificate_id):
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader

    buf = BytesIO()
    w, h = landscape(A4)
    c = canvas.Canvas(buf, pagesize=landscape(A4))

    # Background
    c.setFillColor(colors.HexColor("#0a0e1a"))
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Outer border
    c.setStrokeColor(colors.HexColor("#00d4ff"))
    c.setLineWidth(3)
    c.roundRect(15*mm, 15*mm, w - 30*mm, h - 30*mm, 8*mm, stroke=1, fill=0)

    # Inner border
    c.setStrokeColor(colors.HexColor("#00d4ff"))
    c.setLineWidth(0.5)
    c.setDash(4, 4)
    c.roundRect(20*mm, 20*mm, w - 40*mm, h - 40*mm, 6*mm, stroke=1, fill=0)
    c.setDash()

    # Header accent bar
    c.setFillColor(colors.HexColor("#00d4ff"))
    c.rect(15*mm, h - 35*mm, w - 30*mm, 2*mm, fill=1, stroke=0)

    # PrepIQ branding
    c.setFillColor(colors.HexColor("#00d4ff"))
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(w/2, h - 60*mm, "PREPIQ")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#6b7280"))
    c.drawCentredString(w/2, h - 68*mm, "UK National Cyber Preparedness Learning Platform")

    # Divider
    c.setStrokeColor(colors.HexColor("#1e3a5f"))
    c.setLineWidth(1)
    c.line(60*mm, h - 75*mm, w - 60*mm, h - 75*mm)

    # Certificate of completion
    c.setFillColor(colors.HexColor("#e2e8f0"))
    c.setFont("Helvetica", 13)
    c.drawCentredString(w/2, h - 90*mm, "CERTIFICATE OF COMPLETION")

    # Recipient name
    c.setFillColor(colors.HexColor("#ffffff"))
    c.setFont("Helvetica-Bold", 32)
    c.drawCentredString(w/2, h - 115*mm, name)

    # Line under name
    name_w = c.stringWidth(name, "Helvetica-Bold", 32)
    c.setStrokeColor(colors.HexColor("#00d4ff"))
    c.setLineWidth(1.5)
    c.line(w/2 - name_w/2, h - 118*mm, w/2 + name_w/2, h - 118*mm)

    # Has successfully completed
    c.setFillColor(colors.HexColor("#9ca3af"))
    c.setFont("Helvetica", 12)
    c.drawCentredString(w/2, h - 130*mm, "has successfully completed the learning module")

    # Module title
    c.setFillColor(colors.HexColor("#00d4ff"))
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(w/2, h - 148*mm, module_title)

    # Footer details
    c.setFillColor(colors.HexColor("#6b7280"))
    c.setFont("Helvetica", 9)
    date_str = completed_at.strftime("%d %B %Y")
    c.drawString(30*mm, 30*mm, f"Issued: {date_str}")
    c.drawCentredString(w/2, 30*mm, f"Certificate ID: {certificate_id}")
    c.drawRightString(w - 30*mm, 30*mm, "prepiq.fa3tech.io")

    # Bottom accent bar
    c.setFillColor(colors.HexColor("#00d4ff"))
    c.rect(15*mm, 33*mm, w - 30*mm, 0.5*mm, fill=1, stroke=0)

    c.save()
    return buf.getvalue()
