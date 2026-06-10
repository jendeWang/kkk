import asyncio
import json
from typing import Dict, Set
from fastapi import Request
from starlette.responses import StreamingResponse


class SSEService:
    def __init__(self):
        self._alert_clients: Set[asyncio.Queue] = set()
        self._device_clients: Set[asyncio.Queue] = set()

    async def add_alert_client(self):
        """添加告警SSE客户端"""
        queue = asyncio.Queue()
        self._alert_clients.add(queue)
        return queue

    def remove_alert_client(self, queue: asyncio.Queue):
        """移除告警SSE客户端"""
        self._alert_clients.discard(queue)

    async def add_device_client(self):
        """添加设备状态SSE客户端"""
        queue = asyncio.Queue()
        self._device_clients.add(queue)
        return queue

    def remove_device_client(self, queue: asyncio.Queue):
        """移除设备状态SSE客户端"""
        self._device_clients.discard(queue)

    async def publish_alert(self, data: dict):
        """发布告警事件到所有客户端"""
        message = f"event: new_alert\ndata: {json.dumps({'type': 'new_alert', 'data': data})}\n\n"
        for client in self._alert_clients.copy():
            try:
                await client.put(message)
            except Exception:
                self._alert_clients.discard(client)

    async def publish_device_status(self, data: dict):
        """发布设备状态事件到所有客户端"""
        message = f"event: device_status\ndata: {json.dumps({'type': 'device_status', 'data': data})}\n\n"
        for client in self._device_clients.copy():
            try:
                await client.put(message)
            except Exception:
                self._device_clients.discard(client)


sse_service = SSEService()


async def alert_sse_stream(request: Request):
    """告警SSE端点"""
    queue = await sse_service.add_alert_client()
    try:
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
    """设备状态SSE端点"""
    queue = await sse_service.add_device_client()
    try:
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
