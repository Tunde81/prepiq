"""
EventService: Single interface for all MongoDB event writes.

Usage from any route:
    from app.services.event_service import EventService
    await EventService.track_login(user_id=user.id, ip=request.client.host)

Design principles:
  - Fire-and-forget: all methods are async and safe to call without awaiting in
    background tasks (they catch and log exceptions internally)
  - Never blocks the main request path
  - All timestamps are UTC
"""

from datetime import datetime, timezone
from app.core.mongo import (
    user_events_col, simulation_traces_col,
    ai_coach_logs_col, platform_metrics_col
)
import logging

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class EventService:

    # ─── USER EVENTS ──────────────────────────────────────────────────────────

    @staticmethod
    async def track(
        user_id: int,
        event_type: str,
        metadata: dict | None = None,
        session_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Generic user event tracker. Use specific helpers where possible."""
        try:
            await user_events_col().insert_one({
                "user_id": user_id,
                "event_type": event_type,
                "timestamp": _now(),
                "metadata": metadata or {},
                "session_id": session_id or "",
                "ip_address": ip_address or "",
                "user_agent": user_agent or "",
            })
        except Exception as e:
            logger.warning(f"[EventService] Failed to write user_event: {e}")

    @staticmethod
    async def track_login(user_id: int, ip: str | None = None, user_agent: str | None = None):
        await EventService.track(user_id, "login", ip_address=ip, user_agent=user_agent)

    @staticmethod
    async def track_module_start(user_id: int, module_id: int, module_slug: str):
        await EventService.track(user_id, "module_start", {
            "module_id": module_id,
            "module_slug": module_slug,
        })

    @staticmethod
    async def track_module_complete(user_id: int, module_id: int, module_slug: str, quiz_score: int | None):
        await EventService.track(user_id, "module_complete", {
            "module_id": module_id,
            "module_slug": module_slug,
            "quiz_score": quiz_score,
        })

    @staticmethod
    async def track_quiz_submit(user_id: int, quiz_id: int, module_id: int, score: int, passed: bool):
        await EventService.track(user_id, "quiz_submit", {
            "quiz_id": quiz_id,
            "module_id": module_id,
            "score": score,
            "passed": passed,
        })

    @staticmethod
    async def track_assessment_complete(
        user_id: int, assessment_id: int, overall_score: float, maturity_level: str, sector: str
    ):
        await EventService.track(user_id, "assessment_complete", {
            "assessment_id": assessment_id,
            "overall_score": overall_score,
            "maturity_level": maturity_level,
            "sector": sector,
        })

    @staticmethod
    async def track_report_download(user_id: int, assessment_id: int):
        await EventService.track(user_id, "report_download", {"assessment_id": assessment_id})

    @staticmethod
    async def track_simulation_start(user_id: int, scenario_id: int, session_id: int, scenario_title: str):
        await EventService.track(user_id, "simulation_start", {
            "scenario_id": scenario_id,
            "session_id": session_id or "",
            "scenario_title": scenario_title,
        })

    @staticmethod
    async def track_simulation_complete(
        user_id: int, scenario_id: int, session_id: int, score: int, hints_used: int
    ):
        await EventService.track(user_id, "simulation_complete", {
            "scenario_id": scenario_id,
            "session_id": session_id or "",
            "score": score,
            "hints_used": hints_used,
        })

    # ─── SIMULATION TRACES ────────────────────────────────────────────────────

    @staticmethod
    async def log_simulation_step(
        session_id: int,
        user_id: int,
        scenario_id: int,
        step: int,
        action: str,
        is_correct: bool,
        hint_used: bool,
        time_taken_seconds: int | None = None,
        context: dict | None = None,
    ) -> None:
        try:
            await simulation_traces_col().insert_one({
                "session_id": session_id or "",
                "user_id": user_id,
                "scenario_id": scenario_id,
                "step": step,
                "action": action,
                "is_correct": is_correct,
                "hint_used": hint_used,
                "time_taken_seconds": time_taken_seconds,
                "context": context or {},
                "timestamp": _now(),
            })
        except Exception as e:
            logger.warning(f"[EventService] Failed to write simulation_trace: {e}")

    # ─── AI COACH LOGS ────────────────────────────────────────────────────────

    @staticmethod
    async def log_ai_coach(
        user_id: int,
        session_ref: str,
        role: str,
        content: str,
        context_module: str | None = None,
        tokens_used: int | None = None,
        latency_ms: int | None = None,
    ) -> None:
        try:
            await ai_coach_logs_col().insert_one({
                "user_id": user_id,
                "session_ref": session_ref,
                "role": role,
                "content": content,
                "context_module": context_module,
                "tokens_used": tokens_used,
                "latency_ms": latency_ms,
                "timestamp": _now(),
                "flagged": False,
            })
        except Exception as e:
            logger.warning(f"[EventService] Failed to write ai_coach_log: {e}")

    # ─── PLATFORM METRICS (aggregation writer) ────────────────────────────────

    @staticmethod
    async def upsert_metric(
        period: str,
        period_start: datetime,
        metric_type: str,
        value: float,
        breakdown: dict | None = None,
    ) -> None:
        """Upsert a pre-aggregated metric. Called by background jobs."""
        try:
            await platform_metrics_col().update_one(
                {
                    "period": period,
                    "period_start": period_start,
                    "metric_type": metric_type,
                },
                {
                    "$set": {
                        "value": value,
                        "breakdown": breakdown or {},
                        "computed_at": _now(),
                    }
                },
                upsert=True,
            )
        except Exception as e:
            logger.warning(f"[EventService] Failed to upsert metric: {e}")

    # ─── QUERY HELPERS (for analytics API) ────────────────────────────────────

    @staticmethod
    async def get_user_recent_events(user_id: int, limit: int = 20) -> list:
        try:
            cursor = user_events_col().find(
                {"user_id": user_id},
                {"_id": 0}
            ).sort("timestamp", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.warning(f"[EventService] Failed to query user events: {e}")
            return []

    @staticmethod
    async def get_simulation_trace(session_id: int) -> list:
        try:
            cursor = simulation_traces_col().find(
                {"session_id": session_id},
                {"_id": 0}
            ).sort("step", 1)
            return await cursor.to_list(length=200)
        except Exception as e:
            logger.warning(f"[EventService] Failed to query simulation trace: {e}")
            return []

    @staticmethod
    async def get_platform_metric(metric_type: str, period: str = "daily", limit: int = 30) -> list:
        try:
            cursor = platform_metrics_col().find(
                {"metric_type": metric_type, "period": period},
                {"_id": 0}
            ).sort("period_start", -1).limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.warning(f"[EventService] Failed to query metric: {e}")
            return []

    @staticmethod
    async def count_events_by_type(event_type: str, since: datetime | None = None) -> int:
        try:
            query = {"event_type": event_type}
            if since:
                query["timestamp"] = {"$gte": since}
            return await user_events_col().count_documents(query)
        except Exception as e:
            logger.warning(f"[EventService] Failed to count events: {e}")
            return 0
