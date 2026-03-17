from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, Float,
    ForeignKey, Enum, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    USER = "user"
    ORG_ADMIN = "org_admin"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class Organisation(Base):
    __tablename__ = "organisations"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    sector = Column(String(100))
    size = Column(String(50))  # SME, LARGE, SCHOOL, COUNCIL
    subscription_plan = Column(String(50), default="free")
    is_active = Column(Boolean, default=True)
    invite_code = Column(String(20), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("User", back_populates="organisation")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.USER)
    organisation_id = Column(Integer, ForeignKey("organisations.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    mfa_enabled = Column(Boolean, default=False)
    mfa_secret = Column(String(64), nullable=True)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    organisation = relationship("Organisation", back_populates="users")
    progress = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")
    assessments = relationship("RiskAssessment", back_populates="user", cascade="all, delete-orphan")
    simulation_sessions = relationship("SimulationSession", back_populates="user", cascade="all, delete-orphan")
    badges = relationship("UserBadge", back_populates="user", cascade="all, delete-orphan")


# ─── LEARNING MODELS ─────────────────────────────────────────────────────────

class LearningModule(Base):
    __tablename__ = "learning_modules"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    category = Column(String(100))  # phishing, password, device, browsing, data
    difficulty = Column(String(50))  # beginner, intermediate, advanced
    duration_minutes = Column(Integer, default=15)
    order_index = Column(Integer, default=0)
    is_published = Column(Boolean, default=False)
    content = Column(JSON)  # structured content blocks
    thumbnail_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lessons = relationship("Lesson", back_populates="module", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="module", cascade="all, delete-orphan")
    progress = relationship("UserProgress", back_populates="module")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey("learning_modules.id"))
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Markdown
    order_index = Column(Integer, default=0)
    duration_minutes = Column(Integer, default=5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    module = relationship("LearningModule", back_populates="lessons")


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey("learning_modules.id"))
    title = Column(String(255), nullable=False)
    questions = Column(JSON, nullable=False)  # [{question, options, correct_index, explanation}]
    pass_threshold = Column(Integer, default=70)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    module = relationship("LearningModule", back_populates="quizzes")


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    module_id = Column(Integer, ForeignKey("learning_modules.id"))
    status = Column(String(50), default="not_started")  # not_started, in_progress, completed
    progress_percent = Column(Integer, default=0)
    last_lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    quiz_score = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="progress")
    module = relationship("LearningModule", back_populates="progress")


# ─── RISK ASSESSMENT MODELS ───────────────────────────────────────────────────

class AssessmentDomain(Base):
    __tablename__ = "assessment_domains"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    order_index = Column(Integer, default=0)

    questions = relationship("AssessmentQuestion", back_populates="domain")


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id = Column(Integer, primary_key=True)
    domain_id = Column(Integer, ForeignKey("assessment_domains.id"))
    question_text = Column(Text, nullable=False)
    guidance = Column(Text)
    order_index = Column(Integer, default=0)

    domain = relationship("AssessmentDomain", back_populates="questions")


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    organisation_name = Column(String(255))
    organisation_sector = Column(String(100))
    answers = Column(JSON)   # {question_id: score (0-3)}
    domain_scores = Column(JSON)  # {domain_id: score}
    overall_score = Column(Float)
    maturity_level = Column(String(50))  # critical, low, medium, high, advanced
    top_risks = Column(JSON)  # [{domain, risk, severity, recommendation}]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    report_url = Column(String(500), nullable=True)

    user = relationship("User", back_populates="assessments")


# ─── SIMULATION MODELS ────────────────────────────────────────────────────────

class SimulationScenario(Base):
    __tablename__ = "simulation_scenarios"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True)
    description = Column(Text)
    category = Column(String(100))  # phishing, ransomware, cloud, social_engineering
    difficulty = Column(String(50))
    duration_minutes = Column(Integer, default=20)
    objectives = Column(JSON)  # list of learning objectives
    steps = Column(JSON)       # guided walkthrough steps
    hints = Column(JSON)       # hints for each step
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("SimulationSession", back_populates="scenario")


class SimulationSession(Base):
    __tablename__ = "simulation_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    scenario_id = Column(Integer, ForeignKey("simulation_scenarios.id"))
    status = Column(String(50), default="active")  # active, completed, abandoned
    current_step = Column(Integer, default=0)
    actions_taken = Column(JSON, default=list)
    score = Column(Integer, nullable=True)
    hints_used = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="simulation_sessions")
    scenario = relationship("SimulationScenario", back_populates="sessions")


class UserBadge(Base):
    __tablename__ = "user_badges"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    badge_id = Column(String(50), nullable=False)
    badge_name = Column(String(100), nullable=False)
    badge_description = Column(String(255))
    badge_icon = Column(String(10), default="🏆")
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="badges")
