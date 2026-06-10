from fastapi import APIRouter, Request
from starlette.responses import StreamingResponse
from ..services.sse_service import alert_sse_stream, device_sse_stream

router = APIRouter(prefix="/sse", tags=["SSE推送"])


@router.get("/alerts")
async def sse_alerts(request: Request):
    """告警事件SSE推送"""
    return StreamingResponse(alert_sse_stream(request), media_type="text/event-stream")


@router.get("/devices")
async def sse_devices(request: Request):
    """设备状态SSE推送"""
    return StreamingResponse(device_sse_stream(request), media_type="text/event-stream")
