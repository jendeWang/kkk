from fastapi import APIRouter, Request, Depends
from starlette.responses import StreamingResponse
from .deps import get_current_active_user
from ..models.models import User
from ..services.sse_service import alert_sse_stream, device_sse_stream

router = APIRouter(prefix="/sse", tags=["SSE推送"])


@router.get("/alerts")
async def sse_alerts(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """告警事件SSE推送"""
    return StreamingResponse(alert_sse_stream(request), media_type="text/event-stream")


@router.get("/devices")
async def sse_devices(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """设备状态SSE推送"""
    return StreamingResponse(device_sse_stream(request), media_type="text/event-stream")
