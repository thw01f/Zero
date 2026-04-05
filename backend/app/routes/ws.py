import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sse_starlette.sse import EventSourceResponse
from ..ws_manager import ws_manager, sse_manager
from ..config import settings

router = APIRouter(tags=["realtime"])
logger = logging.getLogger(__name__)


@router.websocket("/ws/{job_id}")
async def websocket_endpoint(job_id: str, ws: WebSocket):
    await ws_manager.connect(job_id, ws)
    # Start Redis pub/sub bridge for this job
    try:
        import redis.asyncio as aioredis
        rc = aioredis.Redis.from_url(settings.redis_url)
        pubsub = rc.pubsub()
        await pubsub.subscribe(f"ws:{job_id}")