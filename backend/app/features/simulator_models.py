"""
PrepIQ - Cyber Incident Simulator Models
Covers: scenarios, simulation sessions, user decisions, timed challenges, AI debrief logs
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.core.database import Base


class SimulatorMode(str, enum.Enum):
    TABLETOP = "tabletop"
    TIMED_CHALLENGE = "timed_challenge"
    AI_DEBRIEF = "ai_debrief"


class SessionStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ScenarioCategory(str, enum.Enum):
    RANSOMWARE = "ransomware"
    PHISHING = "phishing"
    DATA_BREACH = "data_breach"
    INSIDER_THREAT = "insider_threat"
    SUPPLY_CHAIN = "supply_chain"
    DDOS = "ddos"
    BUSINESS_EMAIL_COMPROMISE = "business_email_compromise"
    CLOUD_MISCONFIGURATION = "cloud_misconfiguration"


class DifficultyLevel(str, enum.Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class IncidentScenario(Base):
    """Master scenario library."""
    __tablename__ = "incident_scenarios"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    category = Column(SAEnum(ScenarioCategory), nullable=False)
    difficulty = Column(SAEnum(DifficultyLevel), default=DifficultyLevel.INTERMEDIATE)
    synopsis = Column(Text, nullable=False)          # What happened
    context = Column(JSON, nullable=True)            # org size, sector, assets affected
    initial_inject = Column(Text, nullable=False)    # Opening scenario text
    phases = Column(JSON, nullable=False)            # List of {phase_id, title, inject, choices[]}
    timed_challenges = Column(JSON, nullable=True)   # List of {challenge_id, task, time_limit_seconds, hints, answer_key}
    learning_objectives = Column(JSON, nullable=True)
    frameworks = Column(JSON, nullable=True)         # ["NCSC CAF", "NIST CSF", "ISO 27001"]
    estimated_minutes = Column(Integer, default=30)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("IncidentSimulationSession", back_populates="scenario")


class IncidentSimulationSession(Base):
    """One simulator run per user."""
    __tablename__ = "incident_simulation_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("organisations.id"), nullable=True)
    scenario_id = Column(Integer, ForeignKey("incident_scenarios.id"), nullable=False)
    mode = Column(SAEnum(SimulatorMode), nullable=False)
    status = Column(SAEnum(SessionStatus), default=SessionStatus.ACTIVE)

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    elapsed_seconds = Column(Integer, nullable=True)

    # Scoring
    overall_score = Column(Float, nullable=True)        # 0–100
    decision_score = Column(Float, nullable=True)       # tabletop decisions
    speed_score = Column(Float, nullable=True)          # timed challenge bonus
    communication_score = Column(Float, nullable=True)  # AI debrief quality

    # Decision log
    decisions = Column(JSON, nullable=True)             # [{phase_id, choice_id, rationale, score}]

    # Timed challenge results
    challenge_results = Column(JSON, nullable=True)     # [{challenge_id, answer, time_taken, correct}]

    # AI debrief
    debrief_messages = Column(JSON, nullable=True)      # conversation history
    debrief_feedback = Column(Text, nullable=True)      # final AI feedback summary

    scenario = relationship("IncidentScenario", back_populates="sessions")
    user = relationship("User", backref="incident_simulation_sessions")


class SimulatorLeaderboard(Base):
    """Top scores per scenario."""
    __tablename__ = "simulator_leaderboard"

    id = Column(Integer, primary_key=True)
    scenario_id = Column(Integer, ForeignKey("incident_scenarios.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("incident_simulation_sessions.id"), nullable=False)
    overall_score = Column(Float, nullable=False)
    elapsed_seconds = Column(Integer, nullable=True)
    achieved_at = Column(DateTime(timezone=True), server_default=func.now())

    scenario = relationship("IncidentScenario")
    user = relationship("User")
