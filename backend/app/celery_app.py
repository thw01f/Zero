from celery import Celery
from .config import settings

celery_app = Celery(
    "darklead",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks"],
)
