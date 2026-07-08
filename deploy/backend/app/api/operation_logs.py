from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from datetime import datetime
from .deps import get_current_active_user, get_db
from ..models.models import User
from ..services.operation_log_service import operation_log_service

router = APIRouter(prefix="/operation-logs", tags=["操作日志"])


@router.get("/")
async def list_operation_logs(
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取操作日志列表"""
    result = await operation_log_service.list_logs(
        db=db,
        user_id=current_user.id,
        action=action,
        resource_type=resource_type,
        status=status,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit,
    )
    return {
        "items": [
            {
                "id": log.id,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "description": log.description,
                "ip_address": log.ip_address,
                "status": log.status,
                "error_message": log.error_message,
                "created_at": log.created_at,
            }
            for log in result["items"]
        ],
        "total": result["total"],
        "skip": result["skip"],
        "limit": result["limit"],
    }
