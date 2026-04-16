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

        async def redis_to_ws():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await ws.send_json(data)
                    except Exception:
                        pass

        task = asyncio.create_task(redis_to_ws())
        try:
            while True:
                await ws.receive_text()  # keep alive
        except WebSocketDisconnect:
            pass
        finally:
            task.cancel()
            await pubsub.unsubscribe(f"ws:{job_id}")
            await rc.aclose()
    except Exception as e:
        logger.warning(f"WebSocket bridge error: {e}")
    finally:
        ws_manager.disconnect(job_id, ws)


@router.get("/sse/alerts")
async def sse_alerts():
    q = await sse_manager.subscribe()

    async def event_generator():
        try:
            while True:
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30)
                    yield {"data": json.dumps(event)}
                except asyncio.TimeoutError:
                    yield {"data": json.dumps({"type": "heartbeat"})}
        finally:
            sse_manager.unsubscribe(q)

    return EventSourceResponse(event_generator())
