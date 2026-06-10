from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from .deps import get_current_active_user
from ..database import get_db
from ..models.models import User, Telemetry
from ..schemas import TelemetryResponse

router = APIRouter(prefix="/telemetry", tags=["遥测数据"])


@router.get("/", response_model=List[TelemetryResponse])
async def get_telemetry(
    device_id: int = Query(...),
    property_identifier: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取遥测数据"""
    query = select(Telemetry).where(Telemetry.device_id == device_id)

    if property_identifier:
        query = query.where(Telemetry.property_identifier == property_identifier)
    if start_time:
        query = query.where(Telemetry.timestamp >= start_time)
    if end_time:
        query = query.where(Telemetry.timestamp <= end_time)

    query = query.order_by(Telemetry.timestamp.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()
