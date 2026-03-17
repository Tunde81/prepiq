import httpx
from app.core.config import settings


async def send_email(to: str, subject: str, html: str) -> bool:
    if not settings.RESEND_API_KEY:
        print(f"[Email] Resend not configured - would send to {to}: {subject}")
        return False
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}", "Content-Type": "application/json"},
                json={
                    "from": f"PrepIQ <{settings.MAIL_FROM}>",
                    "to": [to],
                    "subject": subject,
                    "html": html,
                }
            )
            if r.status_code == 200 or r.status_code == 201:
                return True
            print(f"[Email] Resend error {r.status_code}: {r.text}")
            return False
    except Exception as e:
        print(f"[Email] Failed to send to {to}: {e}")
        return False


def welcome_email_html(name: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0a0e1a;color:#e2e8f0;padding:40px;border-radius:12px;">
      <div style="text-align:center;margin-bottom:32px;">
        <h1 style="color:#00d4ff;font-family:monospace;letter-spacing:4px;margin:0;">PREPIQ</h1>
        <p style="color:#6b7280;font-size:12px;margin:4px 0 0;">UK National Cyber Preparedness Learning Platform</p>
      </div>
      <h2 style="color:#ffffff;margin-bottom:8px;">Welcome, {name}!</h2>
      <p style="color:#9ca3af;line-height:1.6;">Your PrepIQ account has been created. You now have access to cybersecurity learning modules, simulations, and risk assessments.</p>
      <div style="margin:32px 0;text-align:center;">
        <a href="https://prepiq.fa3tech.io/dashboard" style="background:#00d4ff;color:#0a0e1a;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:bold;font-family:monospace;">Get Started</a>
      </div>
      <p style="color:#6b7280;font-size:12px;text-align:center;margin-top:32px;border-top:1px solid #1e3a5f;padding-top:16px;">PrepIQ - prepiq.fa3tech.io</p>
    </div>"""


def completion_email_html(name: str, module_title: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0a0e1a;color:#e2e8f0;padding:40px;border-radius:12px;">
      <div style="text-align:center;margin-bottom:32px;">
        <h1 style="color:#00d4ff;font-family:monospace;letter-spacing:4px;margin:0;">PREPIQ</h1>
      </div>
      <div style="text-align:center;margin-bottom:24px;">
        <h2 style="color:#ffffff;margin:0;">Module Complete!</h2>
      </div>
      <p style="color:#9ca3af;line-height:1.6;">Congratulations <strong style="color:#ffffff;">{name}</strong>! You have successfully completed:</p>
      <div style="background:#0d1626;border:1px solid #1e3a5f;border-radius:8px;padding:16px;margin:16px 0;text-align:center;">
        <p style="color:#00d4ff;font-weight:bold;font-size:18px;margin:0;">{module_title}</p>
      </div>
      <p style="color:#9ca3af;line-height:1.6;">Your certificate is available to download from your PrepIQ dashboard.</p>
      <div style="margin:32px 0;text-align:center;">
        <a href="https://prepiq.fa3tech.io/learning" style="background:#00d4ff;color:#0a0e1a;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:bold;font-family:monospace;">Continue Learning</a>
      </div>
      <p style="color:#6b7280;font-size:12px;text-align:center;margin-top:32px;border-top:1px solid #1e3a5f;padding-top:16px;">PrepIQ - prepiq.fa3tech.io</p>
    </div>"""


def verification_email_html(name: str, token: str) -> str:
    verify_url = f"https://prepiq.fa3tech.io/verify?token={token}"
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0a0e1a;color:#e2e8f0;padding:40px;border-radius:12px;">
      <div style="text-align:center;margin-bottom:32px;">
        <h1 style="color:#00d4ff;font-family:monospace;letter-spacing:4px;margin:0;">PREPIQ</h1>
      </div>
      <h2 style="color:#ffffff;">Verify your email</h2>
      <p style="color:#9ca3af;line-height:1.6;">Hi {name}, please verify your email address to activate your PrepIQ account.</p>
      <div style="margin:32px 0;text-align:center;">
        <a href="{verify_url}" style="background:#00d4ff;color:#0a0e1a;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:bold;font-family:monospace;">Verify Email</a>
      </div>
      <p style="color:#6b7280;font-size:12px;">Or copy this link: {verify_url}</p>
      <p style="color:#6b7280;font-size:12px;text-align:center;margin-top:32px;border-top:1px solid #1e3a5f;padding-top:16px;">PrepIQ - prepiq.fa3tech.io</p>
    </div>"""
