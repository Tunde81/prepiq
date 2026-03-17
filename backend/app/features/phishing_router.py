"""
PrepIQ - Phishing Simulation Router
"""
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime, timezone
import secrets

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.email_service import send_email
from app.services.notification_service import notify_phishing_campaign_complete
from app.features.phishing_models import (
    PhishingTemplate, PhishingCampaign, PhishingTarget,
    CampaignStatus, TargetStatus
)

router = APIRouter(prefix="/api/phishing", tags=["phishing"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class CampaignCreate(BaseModel):
    name: str
    template_id: int
    target_emails: List[str]
    target_names: Optional[List[str]] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None


# ── Email builder ─────────────────────────────────────────────────────────────

def build_tracking_url(token: str, domain: str) -> str:
    return f"https://{domain}/phishing/click/{token}"

def build_report_url(token: str, domain: str) -> str:
    return f"https://{domain}/phishing/report/{token}"

def inject_tracking(html: str, click_url: str, report_url: str) -> str:
    """Replace {{CLICK_URL}} and {{REPORT_URL}} placeholders in template."""
    html = html.replace("{{CLICK_URL}}", click_url)
    html = html.replace("{{REPORT_URL}}", report_url)
    return html

async def send_phishing_email(target: PhishingTarget, campaign: PhishingCampaign, template: PhishingTemplate):
    click_url = build_tracking_url(target.tracking_token, campaign.tracking_domain)
    report_url = build_report_url(target.tracking_token, campaign.tracking_domain)
    html = inject_tracking(template.html_body, click_url, report_url)
    subject = template.subject
    if target.name:
        html = html.replace("{{TARGET_NAME}}", target.name.split()[0])
        subject = subject.replace("{{TARGET_NAME}}", target.name.split()[0])
    else:
        html = html.replace("{{TARGET_NAME}}", "there")
        subject = subject.replace("{{TARGET_NAME}}", "there")
    await send_email(target.email, subject, html)


# ── Routes: Templates ─────────────────────────────────────────────────────────

@router.get("/templates")
def list_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    templates = db.query(PhishingTemplate).filter_by(is_active=True).all()
    return [
        {
            "id": t.id, "name": t.name, "category": t.category.value,
            "difficulty": t.difficulty, "sender_name": t.sender_name,
            "sender_email": t.sender_email, "subject": t.subject,
            "description": t.description, "red_flags": t.red_flags,
        }
        for t in templates
    ]


# ── Routes: Campaigns ─────────────────────────────────────────────────────────

@router.get("/campaigns")
def list_campaigns(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    campaigns = db.query(PhishingCampaign).filter_by(
        org_id=current_user.organisation_id
    ).order_by(PhishingCampaign.created_at.desc()).all()
    return [
        {
            "id": c.id, "name": c.name, "status": c.status.value,
            "template": c.template.name if c.template else None,
            "category": c.template.category.value if c.template else None,
            "total_sent": c.total_sent, "total_clicked": c.total_clicked,
            "total_reported": c.total_reported, "total_ignored": c.total_ignored,
            "click_rate": c.click_rate, "report_rate": c.report_rate,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "completed_at": c.completed_at.isoformat() if c.completed_at else None,
        }
        for c in campaigns
    ]


@router.post("/campaigns")
def create_campaign(
    req: CampaignCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    template = db.query(PhishingTemplate).filter_by(id=req.template_id, is_active=True).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    campaign = PhishingCampaign(
        org_id=current_user.organisation_id,
        created_by=current_user.id,
        template_id=req.template_id,
        name=req.name,
        status=CampaignStatus.DRAFT,
    )
    db.add(campaign)
    db.flush()

    for i, email in enumerate(req.target_emails):
        name = req.target_names[i] if req.target_names and i < len(req.target_names) else None
        target = PhishingTarget(
            campaign_id=campaign.id,
            email=email.strip(),
            name=name,
            tracking_token=secrets.token_urlsafe(32),
            status=TargetStatus.PENDING,
        )
        db.add(target)

    db.commit()
    db.refresh(campaign)
    return {"campaign_id": campaign.id, "targets": len(req.target_emails)}


@router.post("/campaigns/{campaign_id}/send")
async def send_campaign(
    campaign_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    campaign = db.query(PhishingCampaign).filter_by(id=campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.PAUSED]:
        raise HTTPException(status_code=400, detail="Campaign already sent or completed")

    template = db.query(PhishingTemplate).filter_by(id=campaign.template_id).first()
    targets = db.query(PhishingTarget).filter_by(
        campaign_id=campaign_id, status=TargetStatus.PENDING
    ).all()

    if not targets:
        raise HTTPException(status_code=400, detail="No pending targets")

    campaign.status = CampaignStatus.ACTIVE
    campaign.started_at = datetime.now(timezone.utc)

    for target in targets:
        target.status = TargetStatus.SENT
        target.sent_at = datetime.now(timezone.utc)
        background_tasks.add_task(send_phishing_email, target, campaign, template)

    campaign.total_sent = len(targets)
    db.commit()

    # Notify campaign creator when all emails sent
    creator = db.query(User).filter_by(id=campaign.created_by).first()
    if creator:
        background_tasks.add_task(
            notify_phishing_campaign_complete,
            admin_email=creator.email,
            admin_name=creator.full_name or creator.email,
            campaign_name=campaign.name,
            total_sent=len(targets),
            total_clicked=0,
            total_reported=0,
            click_rate=0.0,
            report_rate=0.0,
            campaign_id=campaign_id,
        )
    return {"sent": len(targets), "campaign_id": campaign_id}


@router.get("/campaigns/{campaign_id}")
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    campaign = db.query(PhishingCampaign).filter_by(id=campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Not found")

    targets = db.query(PhishingTarget).filter_by(campaign_id=campaign_id).all()
    return {
        "id": campaign.id, "name": campaign.name,
        "status": campaign.status.value,
        "template": {
            "id": campaign.template.id,
            "name": campaign.template.name,
            "category": campaign.template.category.value,
            "difficulty": campaign.template.difficulty,
            "red_flags": campaign.template.red_flags,
        } if campaign.template else None,
        "stats": {
            "total_sent": campaign.total_sent,
            "total_clicked": campaign.total_clicked,
            "total_reported": campaign.total_reported,
            "total_ignored": campaign.total_ignored,
            "click_rate": campaign.click_rate,
            "report_rate": campaign.report_rate,
        },
        "targets": [
            {
                "id": t.id, "email": t.email, "name": t.name,
                "status": t.status.value,
                "sent_at": t.sent_at.isoformat() if t.sent_at else None,
                "clicked_at": t.clicked_at.isoformat() if t.clicked_at else None,
                "reported_at": t.reported_at.isoformat() if t.reported_at else None,
                "training_completed": t.training_completed,
            }
            for t in targets
        ],
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
        "started_at": campaign.started_at.isoformat() if campaign.started_at else None,
    }


@router.delete("/campaigns/{campaign_id}")
def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    campaign = db.query(PhishingCampaign).filter_by(id=campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(campaign)
    db.commit()
    return {"deleted": True}


# ── Tracking endpoints (no auth required) ────────────────────────────────────

@router.get("/click/{token}", response_class=HTMLResponse)
async def track_click(token: str, request: Request, db: Session = Depends(get_db)):
    """Called when a target clicks the phishing link. Records click and serves training page."""
    target = db.query(PhishingTarget).filter_by(tracking_token=token).first()
    if not target:
        return HTMLResponse("<h1>Page not found</h1>", status_code=404)

    if target.status == TargetStatus.SENT:
        target.status = TargetStatus.CLICKED
        target.clicked_at = datetime.now(timezone.utc)
        target.ip_address = request.client.host if request.client else None
        target.user_agent = request.headers.get("user-agent", "")

        campaign = db.query(PhishingCampaign).filter_by(id=target.campaign_id).first()
        if campaign:
            campaign.total_clicked += 1
            total = campaign.total_sent or 1
            campaign.click_rate = round((campaign.total_clicked / total) * 100, 1)

        db.commit()

    # Redirect to training page
    return HTMLResponse(
        f'''<!DOCTYPE html>
<html>
<head>
<meta http-equiv="refresh" content="0;url=https://prepiq.fa3tech.io/phishing/training/{token}" />
</head>
<body>Redirecting...</body>
</html>''',
        status_code=200
    )


@router.get("/report/{token}")
async def track_report(token: str, db: Session = Depends(get_db)):
    """Called when a target reports the phishing email."""
    target = db.query(PhishingTarget).filter_by(tracking_token=token).first()
    if not target:
        raise HTTPException(status_code=404, detail="Not found")

    if target.status in [TargetStatus.SENT, TargetStatus.CLICKED]:
        target.status = TargetStatus.REPORTED
        target.reported_at = datetime.now(timezone.utc)

        campaign = db.query(PhishingCampaign).filter_by(id=target.campaign_id).first()
        if campaign:
            campaign.total_reported += 1
            total = campaign.total_sent or 1
            campaign.report_rate = round((campaign.total_reported / total) * 100, 1)

        db.commit()

    return {"message": "Thank you for reporting this email. Well done!", "reported": True}


@router.get("/training/{token}")
def get_training(token: str, db: Session = Depends(get_db)):
    """Returns training data for the teachable moment page."""
    target = db.query(PhishingTarget).filter_by(tracking_token=token).first()
    if not target:
        raise HTTPException(status_code=404, detail="Not found")

    campaign = db.query(PhishingCampaign).filter_by(id=target.campaign_id).first()
    template = db.query(PhishingTemplate).filter_by(id=campaign.template_id).first() if campaign else None

    target.training_completed = True
    db.commit()

    return {
        "target_name": target.name,
        "template_name": template.name if template else "Phishing Simulation",
        "category": template.category.value if template else "unknown",
        "difficulty": template.difficulty if template else "medium",
        "red_flags": template.red_flags if template else [],
        "clicked": target.clicked_at is not None,
        "campaign_name": campaign.name if campaign else "",
    }


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aggregate stats across all campaigns for the org."""
    campaigns = db.query(PhishingCampaign).filter_by(
        org_id=current_user.organisation_id
    ).all()

    total_sent = sum(c.total_sent for c in campaigns)
    total_clicked = sum(c.total_clicked for c in campaigns)
    total_reported = sum(c.total_reported for c in campaigns)
    avg_click_rate = round(
        sum(c.click_rate for c in campaigns if c.total_sent > 0) /
        max(len([c for c in campaigns if c.total_sent > 0]), 1), 1
    )
    avg_report_rate = round(
        sum(c.report_rate for c in campaigns if c.total_sent > 0) /
        max(len([c for c in campaigns if c.total_sent > 0]), 1), 1
    )

    return {
        "total_campaigns": len(campaigns),
        "active_campaigns": len([c for c in campaigns if c.status.value == "active"]),
        "total_sent": total_sent,
        "total_clicked": total_clicked,
        "total_reported": total_reported,
        "avg_click_rate": avg_click_rate,
        "avg_report_rate": avg_report_rate,
        "campaigns": [
            {
                "id": c.id, "name": c.name, "status": c.status.value,
                "click_rate": c.click_rate, "report_rate": c.report_rate,
                "total_sent": c.total_sent,
            }
            for c in campaigns
        ]
    }


# ── Admin: Seed templates ─────────────────────────────────────────────────────

@router.post("/admin/seed-templates")
def seed_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.value not in ["superadmin", "admin"]:
        raise HTTPException(status_code=403, detail="Admin only")

    existing = db.query(PhishingTemplate).count()
    if existing > 0:
        return {"message": f"Templates already seeded ({existing} found)"}

    templates = [
        {
            "name": "HMRC Tax Refund",
            "category": "hmrc",
            "difficulty": "easy",
            "sender_name": "HMRC Gov UK",
            "sender_email": "noreply@hmrc-gov-uk.com",
            "subject": "You have a tax refund of £{{TARGET_NAME}} waiting",
            "description": "Classic HMRC impersonation offering a fake tax refund. Easy difficulty — obvious red flags.",
            "red_flags": [
                "Sender domain is hmrc-gov-uk.com not hmrc.gov.uk",
                "HMRC never emails about refunds — they use post",
                "Urgent language pressuring immediate action",
                "Link does not go to gov.uk domain",
                "Poor personalisation — uses first name in subject line oddly"
            ],
            "html_body": """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f5f5f5;padding:20px;">
<div style="background:white;border-top:4px solid #00703c;padding:30px;border-radius:4px;">
<img src="https://prepiq.fa3tech.io/static/hmrc-logo.png" alt="HMRC" style="height:40px;margin-bottom:20px;" onerror="this.style.display='none'">
<h2 style="color:#00703c;">HM Revenue & Customs</h2>
<p>Dear {{TARGET_NAME}},</p>
<p>Our records indicate that you are eligible for a <strong>tax refund of £347.50</strong> for the 2024-25 tax year.</p>
<p>To claim your refund, you must verify your identity and bank details within <strong>48 hours</strong> or the refund will be cancelled.</p>
<div style="text-align:center;margin:30px 0;">
<a href="{{CLICK_URL}}" style="background:#00703c;color:white;padding:14px 32px;text-decoration:none;border-radius:4px;font-weight:bold;display:inline-block;">Claim Your Refund Now</a>
</div>
<p style="color:#666;font-size:12px;">If you believe this email is suspicious, <a href="{{REPORT_URL}}">click here to report it</a>.</p>
<hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
<p style="color:#999;font-size:11px;">HM Revenue & Customs, 100 Parliament Street, London SW1A 2BQ</p>
</div>
</body>
</html>"""
        },
        {
            "name": "IT Helpdesk: Password Expiry",
            "category": "it_helpdesk",
            "difficulty": "medium",
            "sender_name": "IT Support",
            "sender_email": "it-support@{{TARGET_NAME}}-helpdesk.co.uk",
            "subject": "Action Required: Your password expires in 24 hours",
            "description": "IT helpdesk impersonation with password expiry urgency. Medium difficulty.",
            "red_flags": [
                "Sender domain does not match your company domain",
                "IT teams rarely email about password expiry with a direct link",
                "Hovering over the button reveals an external URL",
                "Generic greeting without your full name",
                "Artificial 24-hour deadline creates pressure"
            ],
            "html_body": """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;background:#f0f0f0;padding:20px;">
<div style="background:white;padding:32px;border-radius:8px;border:1px solid #ddd;">
<div style="background:#0078d4;padding:16px;margin:-32px -32px 24px;border-radius:8px 8px 0 0;">
<h2 style="color:white;margin:0;font-size:18px;">IT Support Portal</h2>
</div>
<p>Hello {{TARGET_NAME}},</p>
<p>Your network password is due to expire in <strong>24 hours</strong>. To avoid losing access to company systems, please update your password immediately.</p>
<table style="background:#fff3cd;border:1px solid #ffc107;border-radius:4px;padding:12px;width:100%;margin:16px 0;">
<tr><td style="color:#856404;">⚠️ Failure to update your password will result in account lockout and loss of access to email, Teams, and SharePoint.</td></tr>
</table>
<div style="text-align:center;margin:24px 0;">
<a href="{{CLICK_URL}}" style="background:#0078d4;color:white;padding:12px 28px;text-decoration:none;border-radius:4px;font-weight:bold;display:inline-block;">Update Password Now</a>
</div>
<p style="color:#666;font-size:12px;">Think this is suspicious? <a href="{{REPORT_URL}}">Report this email</a> to IT Security.</p>
</div>
</body>
</html>"""
        },
        {
            "name": "Microsoft: Unusual Sign-in Activity",
            "category": "microsoft",
            "difficulty": "medium",
            "sender_name": "Microsoft Account Team",
            "sender_email": "account-security@microsoftonline-alert.com",
            "subject": "Unusual sign-in activity detected on your Microsoft account",
            "description": "Microsoft security alert impersonation. Convincing design but suspicious domain.",
            "red_flags": [
                "Sender domain is microsoftonline-alert.com not microsoft.com",
                "Microsoft security alerts link to account.microsoft.com not third-party sites",
                "The location shown may be fabricated to create alarm",
                "Requests you to click a link rather than going directly to microsoft.com",
                "No personalisation beyond first name"
            ],
            "html_body": """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:'Segoe UI',Arial,sans-serif;max-width:600px;margin:0 auto;background:#f5f5f5;padding:20px;">
<div style="background:white;padding:32px;border-radius:4px;">
<div style="margin-bottom:24px;">
<span style="color:#0078d4;font-size:24px;font-weight:bold;">Microsoft</span>
</div>
<h2 style="color:#323130;font-size:20px;">Unusual sign-in activity</h2>
<p style="color:#323130;">Hello {{TARGET_NAME}},</p>
<p style="color:#605e5c;">We detected a sign-in to your Microsoft account from an unusual location.</p>
<table style="background:#f3f2f1;border-radius:4px;padding:16px;width:100%;margin:16px 0;border-collapse:collapse;">
<tr><td style="padding:4px 0;color:#605e5c;font-size:13px;"><strong>Country/region:</strong></td><td style="color:#323130;font-size:13px;">Russia</td></tr>
<tr><td style="padding:4px 0;color:#605e5c;font-size:13px;"><strong>IP address:</strong></td><td style="color:#323130;font-size:13px;">185.220.101.47</td></tr>
<tr><td style="padding:4px 0;color:#605e5c;font-size:13px;"><strong>Date:</strong></td><td style="color:#323130;font-size:13px;">Today at 03:42 AM</td></tr>
</table>
<p style="color:#605e5c;">If this was you, you can ignore this message. If not, please secure your account immediately.</p>
<div style="text-align:center;margin:24px 0;">
<a href="{{CLICK_URL}}" style="background:#0078d4;color:white;padding:12px 24px;text-decoration:none;border-radius:2px;font-weight:600;display:inline-block;">Review recent activity</a>
</div>
<p style="color:#a19f9d;font-size:11px;">Suspicious email? <a href="{{REPORT_URL}}" style="color:#0078d4;">Report it here</a>.</p>
</div>
</body>
</html>"""
        },
        {
            "name": "CEO Urgent Wire Transfer",
            "category": "ceo_fraud",
            "difficulty": "hard",
            "sender_name": "Babs Adegoke",
            "sender_email": "badegoke@fa3tech-secure.io",
            "subject": "Confidential — urgent payment needed today",
            "description": "CEO fraud / BEC simulation. Hard difficulty — minimal red flags, relies on authority and urgency.",
            "red_flags": [
                "Sender email domain is fa3tech-secure.io not fa3tech.io",
                "CEO rarely requests wire transfers directly via email",
                "Request for secrecy is a major red flag",
                "No reference to internal approval processes",
                "Urgency and confidentiality combined is a classic BEC pattern"
            ],
            "html_body": """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
<p>Hi {{TARGET_NAME}},</p>
<p>I need your help with something urgent and confidential. I am in back-to-back meetings today with a potential acquisition target and need you to process a payment on my behalf.</p>
<p>Please arrange a CHAPS transfer of <strong>£24,500</strong> to the following account:</p>
<p><strong>Account name:</strong> Nexus Advisory Ltd<br>
<strong>Sort code:</strong> 20-45-67<br>
<strong>Account number:</strong> 73829104<br>
<strong>Reference:</strong> CONSULT-2025-Q1</p>
<p>This is time-sensitive — please confirm once done. Keep this between us for now as the deal is not yet public.</p>
<p>I will explain everything after my 4pm call.</p>
<p>Thanks,<br>Babs</p>
<p style="color:#999;font-size:11px;">Think this is suspicious? <a href="{{REPORT_URL}}">Report this email</a> to IT Security immediately.</p>
</body>
</html>"""
        },
        {
            "name": "Royal Mail: Package Delivery Failed",
            "category": "delivery",
            "difficulty": "easy",
            "sender_name": "Royal Mail",
            "sender_email": "delivery@royalmail-notification.co.uk",
            "subject": "Your parcel could not be delivered — action required",
            "description": "Royal Mail delivery failure scam. Easy difficulty — very common template.",
            "red_flags": [
                "Royal Mail domain is royalmail.com not royalmail-notification.co.uk",
                "Royal Mail never charges redelivery fees via email links",
                "No tracking number provided despite claiming to have your parcel",
                "Small fee request is designed to capture payment card details",
                "Generic greeting with no name"
            ],
            "html_body": """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f5f5f5;padding:20px;">
<div style="background:white;padding:30px;border-radius:4px;border-top:4px solid #E30613;">
<h2 style="color:#E30613;">Royal Mail</h2>
<p>Dear Customer,</p>
<p>We attempted to deliver your parcel today but were unable to complete the delivery.</p>
<p>To arrange redelivery, a small <strong>customs clearance fee of £2.99</strong> must be paid within 48 hours, after which your parcel will be returned to the sender.</p>
<div style="background:#f8f8f8;border:1px solid #ddd;padding:16px;margin:16px 0;border-radius:4px;">
<p style="margin:0;font-size:13px;color:#666;">Parcel reference: RM{{TARGET_NAME}}4892UK<br>Delivery attempt: Today<br>Fee due: £2.99</p>
</div>
<div style="text-align:center;margin:24px 0;">
<a href="{{CLICK_URL}}" style="background:#E30613;color:white;padding:12px 28px;text-decoration:none;border-radius:4px;font-weight:bold;display:inline-block;">Pay £2.99 & Redeliver</a>
</div>
<p style="color:#999;font-size:11px;">Think this is a scam? <a href="{{REPORT_URL}}">Report it here</a>.</p>
</div>
</body>
</html>"""
        },
        {
            "name": "NHS: COVID Booster Appointment",
            "category": "nhs",
            "difficulty": "medium",
            "sender_name": "NHS England",
            "sender_email": "appointments@nhs-booking-portal.co.uk",
            "subject": "Your NHS booster appointment is ready to book",
            "description": "NHS appointment booking impersonation. Medium difficulty.",
            "red_flags": [
                "NHS uses nhs.uk domain not nhs-booking-portal.co.uk",
                "NHS never asks for payment card details for bookings",
                "Link goes to external site not nhs.uk",
                "No NHS number referenced despite claiming to know your health records",
                "Urgency of limited slots creates pressure"
            ],
            "html_body": """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#f0f4f5;padding:20px;">
<div style="background:white;padding:30px;border-radius:4px;">
<div style="background:#005eb8;padding:16px;margin:-30px -30px 24px;border-radius:4px 4px 0 0;">
<h2 style="color:white;margin:0;font-size:20px;">NHS</h2>
<p style="color:#aed6f1;margin:4px 0 0;font-size:13px;">National Health Service</p>
</div>
<p>Dear {{TARGET_NAME}},</p>
<p>Your GP surgery has nominated you for a booster vaccination appointment. Slots are limited and must be booked within <strong>72 hours</strong>.</p>
<p>Please confirm your appointment and verify your details to secure your slot.</p>
<div style="text-align:center;margin:24px 0;">
<a href="{{CLICK_URL}}" style="background:#005eb8;color:white;padding:12px 28px;text-decoration:none;border-radius:4px;font-weight:bold;display:inline-block;">Book Your Appointment</a>
</div>
<p style="color:#666;font-size:12px;">Not expecting this? <a href="{{REPORT_URL}}">Report this email as suspicious</a>.</p>
<hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
<p style="color:#999;font-size:11px;">NHS England, PO Box 16738, Redditch, B97 9PT</p>
</div>
</body>
</html>"""
        },
        {
            "name": "LinkedIn: Someone Viewed Your Profile",
            "category": "linkedin",
            "difficulty": "hard",
            "sender_name": "LinkedIn",
            "sender_email": "notifications@linkedln-mail.com",
            "subject": "You appeared in 3 searches this week",
            "description": "LinkedIn notification impersonation. Hard difficulty — very convincing design, subtle domain typo.",
            "red_flags": [
                "Sender domain is linkedln-mail.com (note: ln not in) not linkedin.com",
                "LinkedIn emails come from linkedin.com or e.linkedin.com only",
                "Hovering over buttons reveals non-LinkedIn URLs",
                "Vague claims about who viewed your profile without specifics",
                "Button leads outside linkedin.com"
            ],
            "html_body": """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;max-width:600px;margin:0 auto;background:#f3f2ef;padding:20px;">
<div style="background:white;border-radius:8px;overflow:hidden;">
<div style="background:#0a66c2;padding:16px 24px;">
<span style="color:white;font-size:20px;font-weight:bold;">in</span>
<span style="color:white;font-size:16px;font-weight:600;margin-left:8px;">LinkedIn</span>
</div>
<div style="padding:24px;">
<p style="color:#000;font-size:16px;">Hi {{TARGET_NAME}},</p>
<p style="color:#333;">Your profile is getting noticed. Here is your weekly summary:</p>
<div style="background:#f3f2ef;border-radius:8px;padding:16px;margin:16px 0;">
<p style="margin:0;color:#333;font-size:15px;"><strong>👁 3 people</strong> viewed your profile</p>
<p style="margin:8px 0 0;color:#666;font-size:13px;">Including a Senior Recruiter at a FTSE 100 company</p>
</div>
<div style="text-align:center;margin:24px 0;">
<a href="{{CLICK_URL}}" style="background:#0a66c2;color:white;padding:12px 24px;text-decoration:none;border-radius:24px;font-weight:600;display:inline-block;">See who viewed your profile</a>
</div>
<p style="color:#999;font-size:11px;text-align:center;">Think this is suspicious? <a href="{{REPORT_URL}}" style="color:#0a66c2;">Report this email</a></p>
</div>
</div>
</body>
</html>"""
        },
        {
            "name": "HR: Updated Employee Handbook",
            "category": "hr",
            "difficulty": "hard",
            "sender_name": "Human Resources",
            "sender_email": "hr@internal-hr-portal.co.uk",
            "subject": "Important: Please review and sign the updated employee handbook",
            "description": "HR impersonation requesting document signing. Hard difficulty — routine-seeming request.",
            "red_flags": [
                "Sender domain is not your company domain",
                "Legitimate HR documents are usually shared via your HR system (e.g. Workday, BambooHR)",
                "Request to enter credentials to access a document is a major red flag",
                "No reference to specific policy changes that would explain the update",
                "Deadline pressure for a routine document is unusual"
            ],
            "html_body": """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#f9f9f9;">
<div style="background:white;padding:30px;border-radius:4px;border-left:4px solid #6b48ff;">
<h2 style="color:#333;font-size:18px;">Human Resources</h2>
<p>Dear {{TARGET_NAME}},</p>
<p>As part of our annual policy review, we have updated the Employee Handbook to reflect changes in remote working policy, data protection obligations, and expenses procedures.</p>
<p>All employees are required to <strong>review and digitally sign</strong> the updated handbook by <strong>Friday</strong>. Failure to sign may affect your employment record.</p>
<div style="text-align:center;margin:24px 0;">
<a href="{{CLICK_URL}}" style="background:#6b48ff;color:white;padding:12px 28px;text-decoration:none;border-radius:4px;font-weight:bold;display:inline-block;">Review & Sign Handbook</a>
</div>
<p>If you have any questions, please contact HR.</p>
<p>Kind regards,<br>HR Team</p>
<p style="color:#999;font-size:11px;">Suspicious? <a href="{{REPORT_URL}}">Report this email</a>.</p>
</div>
</body>
</html>"""
        }
    ]

    for t_data in templates:
        t = PhishingTemplate(**t_data)
        db.add(t)

    db.commit()
    return {"message": f"Seeded {len(templates)} phishing templates"}
