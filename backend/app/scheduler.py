import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None


def start_scheduler(app):
    global _scheduler
    from .tasks import monitor_advisories_task, self_health_task
    from .config import settings

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(monitor_advisories_task.delay, "interval",
                       hours=settings.advisory_poll_hours, id="advisory_poll",
                       replace_existing=True)
    _scheduler.add_job(self_health_task.delay, "interval",
                       minutes=settings.self_health_interval_min, id="self_health",
                       replace_existing=True)
    _scheduler.start()
    app.state.scheduler = _scheduler
    logger.info("Scheduler started")


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
