from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.core.mongo import close_mongo, get_event_db
from app.api import auth, users, learning, assessment, simulations, analytics, admin, coach, certificates, scorm, threats, badges, compliance, learning_paths, organisations, board_report, impact, threat_briefing
from app.core.seeder import seed_initial_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await seed_initial_data()
    # Verify MongoDB connectivity (non-fatal — platform works without it)
    try:
        await get_event_db().command("ping")
        print("[MongoDB] ✓ Connected to event store")
    except Exception as e:
        print(f"[MongoDB] ⚠ Could not connect: {e} — events will be skipped")
    yield
    # Shutdown
    await close_mongo()


app = FastAPI(
    title=settings.APP_NAME,
    description="National Cyber Preparedness Learning Platform API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/api/redoc" if settings.APP_ENV != "production" else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (media uploads)
os.makedirs("media", exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(learning.router, prefix="/api/learning", tags=["Learning"])
app.include_router(assessment.router, prefix="/api/assessment", tags=["Assessment"])
app.include_router(simulations.router, prefix="/api/simulations", tags=["Simulations"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(coach.router, prefix="/api/coach", tags=["AI Coach"])
app.include_router(certificates.router, prefix="/api/certificates", tags=["Certificates"])
app.include_router(scorm.router, prefix="/api/import", tags=["SCORM Import"])
app.include_router(threats.router, prefix="/api/threats", tags=["Threat Intelligence"])
app.include_router(badges.router, prefix="/api/badges", tags=["Badges"])
app.include_router(compliance.router, prefix="/api/compliance", tags=["Compliance"])
app.include_router(learning_paths.router, prefix="/api/paths", tags=["Learning Paths"])
app.include_router(organisations.router, prefix="/api/organisations", tags=["Organisations"])
app.include_router(board_report.router, prefix="/api/reports", tags=["Board Reports"])
app.include_router(impact.router, prefix="/api/impact", tags=["Impact"])
app.include_router(threat_briefing.router, prefix="/api/briefing", tags=["Threat Briefing"])
from app.features.health_index_router import router as health_index_router
from app.features.simulator_router import router as simulator_router
from app.features.phishing_router import router as phishing_router
from app.features.notifications_router import router as notifications_router
app.include_router(health_index_router)
app.include_router(simulator_router)
app.include_router(phishing_router)
app.include_router(notifications_router)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME, "version": "1.0.0"}
