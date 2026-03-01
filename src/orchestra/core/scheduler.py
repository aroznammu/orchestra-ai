"""Campaign scheduling via APScheduler.

Registers background jobs for:
  - Daily spend cap resets (midnight UTC)
  - Hourly velocity baseline updates
  - Monthly spend counter resets (1st of month)
"""

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = structlog.get_logger("scheduler")

scheduler = AsyncIOScheduler()

_spend_trackers: dict[str, "SpendTracker"] = {}
_velocity_monitors: dict[str, "SpendVelocityMonitor"] = {}


def register_spend_tracker(tenant_id: str, tracker) -> None:  # noqa: ANN001
    """Register a SpendTracker so the scheduler can reset its daily caps."""
    _spend_trackers[tenant_id] = tracker


def register_velocity_monitor(tenant_id: str, monitor) -> None:  # noqa: ANN001
    """Register a SpendVelocityMonitor so the scheduler can update baselines."""
    _velocity_monitors[tenant_id] = monitor


async def _reset_daily_spend_caps() -> None:
    """Reset daily spend counters for all registered trackers (midnight UTC)."""
    for tenant_id, tracker in _spend_trackers.items():
        try:
            tracker.reset_daily()
            logger.info("daily_spend_reset", tenant_id=tenant_id)
        except Exception as e:
            logger.error("daily_spend_reset_failed", tenant_id=tenant_id, error=str(e))


async def _reset_monthly_spend() -> None:
    """Reset monthly spend counters (1st of month, midnight UTC)."""
    for tenant_id, tracker in _spend_trackers.items():
        try:
            tracker.reset_monthly()
            logger.info("monthly_spend_reset", tenant_id=tenant_id)
        except Exception as e:
            logger.error("monthly_spend_reset_failed", tenant_id=tenant_id, error=str(e))


async def _update_velocity_baselines() -> None:
    """Update velocity baselines for all registered monitors."""
    for tenant_id, monitor in _velocity_monitors.items():
        try:
            monitor.update_baseline()
            logger.debug("velocity_baseline_updated", tenant_id=tenant_id)
        except Exception as e:
            logger.error("velocity_baseline_update_failed", tenant_id=tenant_id, error=str(e))


def start_scheduler() -> None:
    """Start the APScheduler with all registered background jobs."""
    if scheduler.running:
        return

    scheduler.add_job(
        _reset_daily_spend_caps,
        trigger=CronTrigger(hour=0, minute=0, timezone="UTC"),
        id="reset_daily_spend",
        name="Reset daily spend caps (midnight UTC)",
        replace_existing=True,
    )

    scheduler.add_job(
        _reset_monthly_spend,
        trigger=CronTrigger(day=1, hour=0, minute=5, timezone="UTC"),
        id="reset_monthly_spend",
        name="Reset monthly spend counters (1st of month)",
        replace_existing=True,
    )

    scheduler.add_job(
        _update_velocity_baselines,
        trigger=IntervalTrigger(hours=1),
        id="update_velocity_baselines",
        name="Update spend velocity baselines (hourly)",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "scheduler_started",
        jobs=[j.id for j in scheduler.get_jobs()],
    )


def stop_scheduler() -> None:
    """Shut down the scheduler gracefully."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("scheduler_stopped")


def get_registered_jobs() -> list[dict]:
    """Return info about all registered jobs (for status/debugging)."""
    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger),
        }
        for job in scheduler.get_jobs()
    ]
