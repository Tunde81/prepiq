"""
PrepIQ - Phishing Simulation Module Models
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class CampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


class TemplateCategory(str, enum.Enum):
    HMRC = "hmrc"
    NHS = "nhs"
    NATWEST = "natwest"
    MICROSOFT = "microsoft"
    DVLA = "dvla"
    IT_HELPDESK = "it_helpdesk"
    HR = "hr"
    CEO_FRAUD = "ceo_fraud"
    DELIVERY = "delivery"
    LINKEDIN = "linkedin"


class TargetStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    CLICKED = "clicked"
    REPORTED = "reported"
    IGNORED = "ignored"


class PhishingTemplate(Base):
    """Library of phishing email templates."""
    __tablename__ = "phishing_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    category = Column(SAEnum(TemplateCategory), nullable=False)
    difficulty = Column(String(20), default="medium")  # easy | medium | hard
    sender_name = Column(String(100), nullable=False)
    sender_email = Column(String(200), nullable=False)
    subject = Column(String(300), nullable=False)
    html_body = Column(Text, nullable=False)
    red_flags = Column(JSON, nullable=True)   # list of red flag descriptions for training
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    campaigns = relationship("PhishingCampaign", back_populates="template")


class PhishingCampaign(Base):
    """A phishing simulation campaign."""
    __tablename__ = "phishing_campaigns"

    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organisations.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("phishing_templates.id"), nullable=False)
    name = Column(String(200), nullable=False)
    status = Column(SAEnum(CampaignStatus), default=CampaignStatus.DRAFT)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    tracking_domain = Column(String(200), default="prepiq.fa3tech.io")

    # Stats cache
    total_sent = Column(Integer, default=0)
    total_clicked = Column(Integer, default=0)
    total_reported = Column(Integer, default=0)
    total_ignored = Column(Integer, default=0)
    click_rate = Column(Float, default=0.0)
    report_rate = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    template = relationship("PhishingTemplate", back_populates="campaigns")
    targets = relationship("PhishingTarget", back_populates="campaign", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])


class PhishingTarget(Base):
    """Individual target within a campaign."""
    __tablename__ = "phishing_targets"

    id = Column(Integer, primary_key=True)
    campaign_id = Column(Integer, ForeignKey("phishing_campaigns.id"), nullable=False)
    email = Column(String(200), nullable=False)
    name = Column(String(200), nullable=True)
    tracking_token = Column(String(64), unique=True, nullable=False)
    status = Column(SAEnum(TargetStatus), default=TargetStatus.PENDING)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    reported_at = Column(DateTime(timezone=True), nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(300), nullable=True)
    training_completed = Column(Boolean, default=False)

    campaign = relationship("PhishingCampaign", back_populates="targets")
