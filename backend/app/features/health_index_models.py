"""
PrepIQ - UK SME Cyber Health Index Models
Covers: assessment sessions, question responses, scored results, benchmarks
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

# Import your existing Base from db.py
from app.core.database import Base


class RiskTier(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    SECURE = "secure"


class AssessmentStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"


class HealthDomain(str, enum.Enum):
    GOVERNANCE = "governance"
    ASSET_MANAGEMENT = "asset_management"
    ACCESS_CONTROL = "access_control"
    NETWORK_SECURITY = "network_security"
    INCIDENT_RESPONSE = "incident_response"
    SUPPLY_CHAIN = "supply_chain"
    STAFF_AWARENESS = "staff_awareness"
    DATA_PROTECTION = "data_protection"
    PATCHING = "patching"
    BACKUP_RECOVERY = "backup_recovery"


class HealthIndexQuestion(Base):
    """Master question bank for the health assessment."""
    __tablename__ = "health_index_questions"

    id = Column(Integer, primary_key=True)
    domain = Column(SAEnum(HealthDomain), nullable=False)
    question_text = Column(Text, nullable=False)
    help_text = Column(Text, nullable=True)
    answer_type = Column(String(20), default="likert5")  # likert5 | boolean | multi_choice
    options = Column(JSON, nullable=True)       # for multi_choice
    weight = Column(Float, default=1.0)         # scoring weight within domain
    ncsc_reference = Column(String(100), nullable=True)   # e.g. "Cyber Essentials: Firewalls"
    fca_reference = Column(String(100), nullable=True)    # e.g. "SYSC 13.7"
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    responses = relationship("HealthIndexResponse", back_populates="question")


class HealthIndexAssessment(Base):
    """One assessment run per org per period."""
    __tablename__ = "health_index_assessments"

    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organisations.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SAEnum(AssessmentStatus), default=AssessmentStatus.IN_PROGRESS)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Aggregate scores (populated on completion)
    overall_score = Column(Float, nullable=True)           # 0–100
    risk_tier = Column(SAEnum(RiskTier), nullable=True)
    domain_scores = Column(JSON, nullable=True)            # {domain: score}
    benchmark_percentile = Column(Float, nullable=True)   # vs UK SME cohort
    recommendations = Column(JSON, nullable=True)         # prioritised action list

    # Metadata
    employee_count = Column(String(20), nullable=True)    # <10 | 10-49 | 50-249
    sector = Column(String(100), nullable=True)
    has_it_team = Column(Boolean, nullable=True)
    has_cyber_insurance = Column(Boolean, nullable=True)

    responses = relationship("HealthIndexResponse", back_populates="assessment",
                             cascade="all, delete-orphan")
    org = relationship("Organisation", backref="health_assessments")
    user = relationship("User", backref="health_assessments")


class HealthIndexResponse(Base):
    """Individual question answer within an assessment."""
    __tablename__ = "health_index_responses"

    id = Column(Integer, primary_key=True)
    assessment_id = Column(Integer, ForeignKey("health_index_assessments.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("health_index_questions.id"), nullable=False)
    answer_value = Column(String(200), nullable=False)    # raw answer
    score_contribution = Column(Float, nullable=True)     # computed contribution
    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    assessment = relationship("HealthIndexAssessment", back_populates="responses")
    question = relationship("HealthIndexQuestion", back_populates="responses")


class HealthIndexBenchmark(Base):
    """Anonymised aggregate benchmark data by sector and size."""
    __tablename__ = "health_index_benchmarks"

    id = Column(Integer, primary_key=True)
    sector = Column(String(100), nullable=True)
    employee_band = Column(String(20), nullable=True)
    domain = Column(SAEnum(HealthDomain), nullable=True)  # null = overall
    avg_score = Column(Float, nullable=False)
    p25_score = Column(Float, nullable=False)
    p50_score = Column(Float, nullable=False)
    p75_score = Column(Float, nullable=False)
    sample_size = Column(Integer, default=0)
    period = Column(String(7), nullable=False)    # e.g. "2025-Q1"
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
