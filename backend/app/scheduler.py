import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None


def _advisory_runner():
    """Run advisory monitor directly (no Celery required)."""
    import asyncio, threading
    from .tasks import _monitor_advisories
    def _run():
        try:
            asyncio.run(_monitor_advisories())
        except Exception as e:
            logger.warning(f"Advisory poll failed: {e}")
    threading.Thread(target=_run, daemon=True).start()


def start_scheduler(app):
    global _scheduler
    from .config import settings

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(_advisory_runner, "interval",
                       hours=settings.advisory_poll_hours, id="advisory_poll",
                       replace_existing=True)
    # Run advisory fetch immediately on startup
    _scheduler.add_job(_advisory_runner, "date", id="advisory_startup")
    _scheduler.start()
    app.state.scheduler = _scheduler
    logger.info("Scheduler started")


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
