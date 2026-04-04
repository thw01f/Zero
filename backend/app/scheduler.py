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