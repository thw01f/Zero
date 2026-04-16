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