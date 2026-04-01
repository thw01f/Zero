import asyncio
import json
import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WsManager:
    def __init__(self):
        self.active: Dict[str, List[WebSocket]] = {}

    async def connect(self, job_id: str, ws: WebSocket):
        await ws.accept()
        self.active.setdefault(job_id, []).append(ws)

    def disconnect(self, job_id: str, ws: WebSocket):
        if job_id in self.active:
            self.active[job_id] = [w for w in self.active[job_id] if w != ws]

    async def broadcast(self, job_id: str, message: dict):
        if job_id not in self.active:
            return
        dead = []
        for ws in self.active[job_id]:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(job_id, ws)


class SseManager:
    def __init__(self):
        self.subscribers: List[asyncio.Queue] = []

    async def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self.subscribers = [s for s in self.subscribers if s != q]

    async def publish(self, event: dict):
        dead = []
        for q in self.subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self.unsubscribe(q)


ws_manager = WsManager()
sse_manager = SseManager()
