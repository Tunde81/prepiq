"""
PrepIQ - Notification Service
Handles all transactional email notifications:
- Course completion
- Certificate ready
- Badge earned
- Weekly learning reminder
- Health Index / Assessment reminder
"""
from app.services.email_service import send_email
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://prepiq.fa3tech.io"

# ── Shared email wrapper ──────────────────────────────────────────────────────

def _base_html(content: str, footer_note: str = "") -> str:
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#0a0e1a;font-family:Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0e1a;padding:40px 20px;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background:#0d1626;border-radius:12px;border:1px solid #1e3a5f;overflow:hidden;">
  <tr><td style="background:#0a0e1a;padding:24px 32px;border-bottom:1px solid #1e3a5f;">
    <h1 style="color:#00d4ff;font-family:monospace;letter-spacing:4px;margin:0;font-size:22px;">PREPIQ</h1>
    <p style="color:#6b7280;font-size:11px;margin:4px 0 0;">UK National Cyber Preparedness Learning Platform</p>
  </td></tr>
  <tr><td style="padding:32px;">
    {content}
  </td></tr>
  <tr><td style="padding:16px 32px;border-top:1px solid #1e3a5f;text-align:center;">
    <p style="color:#4b5563;font-size:11px;margin:0;">
      PrepIQ &nbsp;·&nbsp; <a href="{BASE_URL}" style="color:#00d4ff;text-decoration:none;">prepiq.fa3tech.io</a>
      {"&nbsp;·&nbsp;" + footer_note if footer_note else ""}
    </p>
  </td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""


def _cta_button(text: str, url: str, color: str = "#00d4ff") -> str:
    text_color = "#0a0e1a" if color == "#00d4ff" else "white"
    return f'''<div style="text-align:center;margin:28px 0;">
<a href="{url}" style="background:{color};color:{text_color};padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:bold;font-family:monospace;font-size:14px;display:inline-block;">{text}</a>
</div>'''


# ── 1. Course completion notification ─────────────────────────────────────────

async def notify_course_completion(
    user_email: str,
    user_name: str,
    module_title: str,
    module_id: int,
    quiz_score: int | None = None,
):
    first_name = user_name.split()[0] if user_name else "there"
    score_block = ""
    if quiz_score is not None:
        score_color = "#22c55e" if quiz_score >= 70 else "#eab308"
        score_block = f'''<div style="background:#0a0e1a;border:1px solid #1e3a5f;border-radius:8px;padding:16px;margin:16px 0;text-align:center;">
<p style="color:#9ca3af;font-size:12px;margin:0 0 4px;text-transform:uppercase;letter-spacing:1px;">Quiz Score</p>
<p style="color:{score_color};font-size:32px;font-weight:bold;margin:0;font-family:monospace;">{quiz_score}%</p>
</div>'''

    content = f'''
<h2 style="color:#ffffff;margin:0 0 8px;">🎉 Module Complete!</h2>
<p style="color:#9ca3af;line-height:1.6;">Well done, <strong style="color:#ffffff;">{first_name}</strong>! You have successfully completed:</p>
<div style="background:#0a0e1a;border:1px solid #00d4ff;border-radius:8px;padding:20px;margin:16px 0;text-align:center;">
<p style="color:#00d4ff;font-weight:bold;font-size:18px;margin:0;">{module_title}</p>
</div>
{score_block}
<p style="color:#9ca3af;line-height:1.6;">Your certificate of completion is now available to download from your dashboard.</p>
{_cta_button("Download Certificate", f"{BASE_URL}/learning/{module_id}/certificate")}
<p style="color:#6b7280;font-size:13px;">Keep going — consistency is the key to building a strong cyber security posture. Check out what is next in your learning path.</p>
{_cta_button("Continue Learning", f"{BASE_URL}/learning", "#6366f1")}
'''
    await send_email(
        to=user_email,
        subject=f"✅ You completed: {module_title}",
        html=_base_html(content)
    )


# ── 2. Certificate ready notification ────────────────────────────────────────

async def notify_certificate_ready(
    user_email: str,
    user_name: str,
    module_title: str,
    module_id: int,
    certificate_id: str,
):
    first_name = user_name.split()[0] if user_name else "there"
    content = f'''
<h2 style="color:#ffffff;margin:0 0 8px;">📜 Your Certificate is Ready</h2>
<p style="color:#9ca3af;line-height:1.6;">Congratulations, <strong style="color:#ffffff;">{first_name}</strong>! Your certificate of completion for <strong style="color:#00d4ff;">{module_title}</strong> is now ready.</p>
<div style="background:#0a0e1a;border:1px solid #1e3a5f;border-radius:8px;padding:20px;margin:20px 0;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td style="color:#6b7280;font-size:12px;text-transform:uppercase;letter-spacing:1px;padding-bottom:8px;">Certificate ID</td>
    </tr>
    <tr>
      <td style="color:#00d4ff;font-family:monospace;font-size:16px;font-weight:bold;">{certificate_id}</td>
    </tr>
  </table>
</div>
<p style="color:#9ca3af;line-height:1.6;">This certificate can be shared on LinkedIn or included in your professional portfolio as evidence of continuing professional development in cybersecurity.</p>
{_cta_button("Download Certificate PDF", f"{BASE_URL}/certificates/{module_id}")}
'''
    await send_email(
        to=user_email,
        subject=f"📜 Your PrepIQ certificate for {module_title} is ready",
        html=_base_html(content)
    )


# ── 3. Badge earned notification ─────────────────────────────────────────────

async def notify_badge_earned(
    user_email: str,
    user_name: str,
    badge_icon: str,
    badge_name: str,
    badge_description: str,
    total_badges: int,
):
    first_name = user_name.split()[0] if user_name else "there"
    content = f'''
<h2 style="color:#ffffff;margin:0 0 8px;">🏅 New Badge Earned!</h2>
<p style="color:#9ca3af;line-height:1.6;">Great work, <strong style="color:#ffffff;">{first_name}</strong>! You have just earned a new badge:</p>
<div style="background:#0a0e1a;border:1px solid #6366f1;border-radius:12px;padding:28px;margin:20px 0;text-align:center;">
  <p style="font-size:52px;margin:0 0 12px;">{badge_icon}</p>
  <p style="color:#ffffff;font-weight:bold;font-size:20px;margin:0 0 6px;">{badge_name}</p>
  <p style="color:#9ca3af;font-size:14px;margin:0;">{badge_description}</p>
</div>
<p style="color:#9ca3af;line-height:1.6;text-align:center;">You now have <strong style="color:#6366f1;">{total_badges} badge{"s" if total_badges != 1 else ""}</strong> on your PrepIQ profile.</p>
{_cta_button("View Your Badges", f"{BASE_URL}/dashboard", "#6366f1")}
'''
    await send_email(
        to=user_email,
        subject=f"{badge_icon} You earned the {badge_name} badge on PrepIQ!",
        html=_base_html(content)
    )


# ── 4. Weekly learning reminder ───────────────────────────────────────────────

async def notify_weekly_reminder(
    user_email: str,
    user_name: str,
    modules_completed: int,
    streak_days: int = 0,
    suggested_module: str | None = None,
):
    first_name = user_name.split()[0] if user_name else "there"
    suggestion_block = ""
    if suggested_module:
        suggestion_block = f'''
<div style="background:#0a0e1a;border:1px solid #1e3a5f;border-radius:8px;padding:16px;margin:16px 0;">
  <p style="color:#6b7280;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:0 0 6px;">Suggested Next Module</p>
  <p style="color:#00d4ff;font-weight:bold;margin:0;">{suggested_module}</p>
</div>'''

    content = f'''
<h2 style="color:#ffffff;margin:0 0 8px;">👋 Weekly Check-In</h2>
<p style="color:#9ca3af;line-height:1.6;">Hi <strong style="color:#ffffff;">{first_name}</strong>, just a friendly nudge from PrepIQ.</p>
<div style="display:flex;gap:16px;margin:20px 0;">
  <div style="background:#0a0e1a;border:1px solid #1e3a5f;border-radius:8px;padding:16px;text-align:center;flex:1;">
    <p style="color:#6b7280;font-size:12px;margin:0 0 4px;text-transform:uppercase;letter-spacing:1px;">Modules Completed</p>
    <p style="color:#00d4ff;font-size:28px;font-weight:bold;margin:0;font-family:monospace;">{modules_completed}</p>
  </div>
</div>
{suggestion_block}
<p style="color:#9ca3af;line-height:1.6;">Regular practice is the most effective way to build lasting cyber security knowledge. Even 15 minutes a week makes a measurable difference.</p>
{_cta_button("Continue Learning", f"{BASE_URL}/learning")}
'''
    await send_email(
        to=user_email,
        subject="📚 Your weekly PrepIQ learning reminder",
        html=_base_html(content, "You are receiving this because you have a PrepIQ account.")
    )


# ── 5. Health Index / Assessment reminder ────────────────────────────────────

async def notify_assessment_reminder(
    user_email: str,
    user_name: str,
    assessment_type: str = "Health Index",
    last_completed: str | None = None,
    days_since: int | None = None,
):
    first_name = user_name.split()[0] if user_name else "there"
    last_block = ""
    if last_completed and days_since:
        last_block = f'''<p style="color:#9ca3af;line-height:1.6;">Your last assessment was completed on <strong style="color:#ffffff;">{last_completed}</strong> — {days_since} days ago.</p>'''

    content = f'''
<h2 style="color:#ffffff;margin:0 0 8px;">🔔 Time for Your {assessment_type}</h2>
<p style="color:#9ca3af;line-height:1.6;">Hi <strong style="color:#ffffff;">{first_name}</strong>, it is time to reassess your cyber security posture.</p>
{last_block}
<p style="color:#9ca3af;line-height:1.6;">Regular assessments help you track your improvement, identify new gaps, and demonstrate compliance with NCSC Cyber Essentials, UK GDPR, and FCA requirements.</p>
<div style="background:#0a0e1a;border:1px solid #fbbf24;border-radius:8px;padding:16px;margin:16px 0;">
  <p style="color:#fbbf24;font-weight:bold;margin:0 0 4px;">⏱ Takes approximately 10 minutes</p>
  <p style="color:#9ca3af;font-size:13px;margin:0;">Your results are benchmarked against UK SMEs in your sector.</p>
</div>
{_cta_button("Start Assessment", f"{BASE_URL}/health-index", "#fbbf24")}
'''
    await send_email(
        to=user_email,
        subject=f"🔔 Time to run your PrepIQ {assessment_type}",
        html=_base_html(content, "You are receiving this as a PrepIQ platform user.")
    )


# ── 6. Phishing simulation result (for admin) ────────────────────────────────

async def notify_phishing_campaign_complete(
    admin_email: str,
    admin_name: str,
    campaign_name: str,
    total_sent: int,
    total_clicked: int,
    total_reported: int,
    click_rate: float,
    report_rate: float,
    campaign_id: int,
):
    first_name = admin_name.split()[0] if admin_name else "there"
    click_color = "#22c55e" if click_rate < 20 else "#eab308" if click_rate < 40 else "#ef4444"
    report_color = "#22c55e" if report_rate > 30 else "#eab308"

    content = f'''
<h2 style="color:#ffffff;margin:0 0 8px;">🎣 Phishing Campaign Complete</h2>
<p style="color:#9ca3af;line-height:1.6;">Hi <strong style="color:#ffffff;">{first_name}</strong>, your phishing simulation campaign <strong style="color:#00d4ff;">{campaign_name}</strong> has concluded.</p>
<div style="background:#0a0e1a;border:1px solid #1e3a5f;border-radius:8px;padding:20px;margin:20px 0;">
  <table width="100%" cellpadding="8" cellspacing="0">
    <tr>
      <td style="color:#6b7280;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Emails Sent</td>
      <td style="color:#ffffff;font-weight:bold;text-align:right;font-family:monospace;">{total_sent}</td>
    </tr>
    <tr>
      <td style="color:#6b7280;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Clicked Link</td>
      <td style="color:{click_color};font-weight:bold;text-align:right;font-family:monospace;">{total_clicked} ({click_rate}%)</td>
    </tr>
    <tr>
      <td style="color:#6b7280;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Reported as Phishing</td>
      <td style="color:{report_color};font-weight:bold;text-align:right;font-family:monospace;">{total_reported} ({report_rate}%)</td>
    </tr>
  </table>
</div>
<p style="color:#9ca3af;line-height:1.6;">{"✅ Good result — click rate is below 20%. Continue regular simulations to maintain resilience." if click_rate < 20 else "⚠️ Click rate above 20% — consider additional phishing awareness training for your team."}</p>
{_cta_button("View Full Campaign Report", f"{BASE_URL}/phishing?campaign={campaign_id}")}
'''
    await send_email(
        to=admin_email,
        subject=f"🎣 Phishing campaign complete: {campaign_name} — {click_rate}% click rate",
        html=_base_html(content)
    )
