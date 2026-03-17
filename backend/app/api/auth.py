from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone, timedelta
import secrets
import random

from app.core.database import get_db
from app.core.security import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token, get_current_user
)
from app.core.config import settings
from app.models.user import User, UserRole
from app.services.event_service import EventService
from app.services.email_service import send_email

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str
    full_name: str
    organisation_name: str | None = None

class OTPVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

class RefreshRequest(BaseModel):
    refresh_token: str


# ─── Email helpers ────────────────────────────────────────────────────────────

def otp_email_html(name: str, otp: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;background:#0a0e1a;color:#e2e8f0;padding:40px;border-radius:12px;">
      <div style="text-align:center;margin-bottom:32px;">
        <h1 style="color:#00d4ff;font-family:monospace;letter-spacing:4px;margin:0;">PREPIQ</h1>
        <p style="color:#6b7280;font-size:12px;margin:4px 0 0;">UK National Cyber Preparedness Learning Platform</p>
      </div>
      <h2 style="color:#ffffff;margin-bottom:8px;">Verify your account, {name.split()[0]}!</h2>
      <p style="color:#9ca3af;line-height:1.6;">Use the OTP below to complete your registration. It expires in <strong style="color:#ffffff;">10 minutes</strong>.</p>
      <div style="margin:32px 0;text-align:center;">
        <div style="display:inline-block;background:#0d1321;border:2px solid #00d4ff;border-radius:12px;padding:24px 48px;">
          <p style="color:#6b7280;font-size:12px;font-family:monospace;letter-spacing:2px;margin:0 0 8px;">VERIFICATION CODE</p>
          <p style="color:#00d4ff;font-size:42px;font-family:monospace;font-weight:bold;letter-spacing:12px;margin:0;">{otp}</p>
        </div>
      </div>
      <p style="color:#6b7280;font-size:12px;text-align:center;">If you did not create a PrepIQ account, you can safely ignore this email.</p>
    </div>
    """


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/register", response_model=dict, status_code=201)
async def register(
    payload: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Confirm password match
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    # Password strength
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    # Duplicate email check
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Generate 6-digit OTP + expiry
    otp = str(random.randint(100000, 999999))
    otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=10)

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        verification_token=otp,
        is_verified=False,
        is_active=True,
        role=UserRole.USER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Send OTP email
    background_tasks.add_task(
        send_email,
        payload.email,
        "Your PrepIQ verification code",
        otp_email_html(payload.full_name, otp)
    )

    return {
        "message": "Registration successful. Please check your email for your 6-digit verification code.",
        "user_id": user.id,
        "email": user.email
    }


@router.post("/verify-otp", response_model=dict)
async def verify_otp(
    payload: OTPVerifyRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Account not found")
    if user.is_verified:
        return {"message": "Account already verified. Please log in."}
    if user.verification_token != payload.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP. Please check your email and try again.")

    user.is_verified = True
    user.verification_token = None
    db.commit()

    return {"message": "Email verified successfully. You can now log in."}


@router.post("/resend-otp", response_model=dict)
async def resend_otp(
    email: EmailStr,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Account not found")
    if user.is_verified:
        raise HTTPException(status_code=400, detail="Account already verified")

    otp = str(random.randint(100000, 999999))
    user.verification_token = otp
    db.commit()

    background_tasks.add_task(
        send_email,
        email,
        "Your new PrepIQ verification code",
        otp_email_html(user.full_name, otp)
    )

    return {"message": "New OTP sent to your email."}


@router.post("/login", response_model=TokenResponse)
async def login(
    background_tasks: BackgroundTasks,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated. Please contact support.")
    if not user.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Email not verified. Please check your inbox for the 6-digit OTP."
        )

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    background_tasks.add_task(
        EventService.track_login,
        user_id=user.id,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_verified": user.is_verified,
        }
    )


@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Legacy token verification — kept for backwards compatibility."""
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user.is_verified = True
    user.verification_token = None
    db.commit()
    return {"message": "Email verified successfully"}


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_verified": current_user.is_verified,
        "organisation_id": current_user.organisation_id,
    }
