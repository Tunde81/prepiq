"""
MongoDB connection for PrepIQ event store.
Uses motor (async) driver — non-blocking, plays nicely with FastAPI.

Collections:
  - user_events         : activity stream (logins, module starts/completions, quiz submits)
  - simulation_traces   : per-step action logs for simulations
  - ai_coach_logs       : AI coach conversation turns
  - platform_metrics    : pre-aggregated dashboard metrics
  - threat_intel_feed   : imported threat intelligence items
"""

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(
            settings.MONGO_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
    return _client


def get_event_db():
    """Returns the prepiq_events database handle."""
    return get_mongo_client().prepiq_events


async def close_mongo():
    global _client
    if _client:
        _client.close()
        _client = None


# Convenience collection accessors
def user_events_col():
    return get_event_db().user_events

def simulation_traces_col():
    return get_event_db().simulation_traces

def ai_coach_logs_col():
    return get_event_db().ai_coach_logs

def platform_metrics_col():
    return get_event_db().platform_metrics

def threat_intel_col():
    return get_event_db().threat_intel_feed
