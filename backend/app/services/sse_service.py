import asyncio
import json
from fastapi import Request
from fastapi.responses import StreamingResponse
from typing import Dict, Set


class SSEService:
    def __init__(self):
        self._alert_clients: Set[asyncio.Queue] = set()
        self._device_clients: Set[asyncio.Queue] = set()
        self._alert_lock = asyncio.Lock()
        self._device_lock = asyncio.Lock()

    async def add_alert_client(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        async with self._alert_lock:
            self._alert_clients.add(queue)
        return queue

    def remove_alert_client(self, queue: asyncio.Queue):
        self._alert_clients.discard(queue)

    async def add_device_client(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        async with self._device_lock:
            self._device_clients.add(queue)
        return queue

    def remove_device_client(self, queue: asyncio.Queue):
        self._device_clients.discard(queue)

    async def publish_alert(self, data: dict):
        message = f"event: new_alert\ndata: {json.dumps({'type': 'new_alert', 'data': data})}\n\n"
        async with self._alert_lock:
            for q in list(self._alert_clients):
                try:
                    await q.put(message)
                except Exception:
                    pass

    async def publish_device_status(self, data: dict):
        message = f"event: device_status\ndata: {json.dumps({'type': 'device_status', 'data': data})}\n\n"
        async with self._device_lock:
            for q in list(self._device_clients):
                try:
                    await q.put(message)
                except Exception:
                    pass


sse_service = SSEService()


async def alert_sse_stream(request: Request):
    queue = await sse_service.add_alert_client()
    try:
        yield f": keepalive session started\n\n"
        while True:
            if await request.is_disconnected():
                break
            try:
                message = await asyncio.wait_for(queue.get(), timeout=30)
                yield message
            except asyncio.TimeoutError:
                yield f": keepalive\n\n"
    finally:
        sse_service.remove_alert_client(queue)


async def device_sse_stream(request: Request):
    queue = await sse_service.add_device_client()
    try:
        yield f": keepalive session started\n\n"
        while True:
            if await request.is_disconnected():
                break
            try:
                message = await asyncio.wait_for(queue.get(), timeout=30)
                yield message
            except asyncio.TimeoutError:
                yield f": keepalive\n\n"
    finally:
        sse_service.remove_device_client(queue)
