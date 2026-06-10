from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional, Dict, Any
from datetime import datetime

from .deps import get_current_active_user, get_db
from ..models.models import Telemetry, Device, User
from ..schemas import TelemetryResponse

router = APIRouter(prefix="/telemetry", tags=["遥测数据"])


@router.get("/", response_model=Dict[str, Any])
async def list_telemetry(
    device_id: Optional[int] = Query(None),
    property_identifier: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """列出遥测数据（支持过滤和分页）"""
    query = select(Telemetry).join(Device).where(Device.owner_id == current_user.id)

    if device_id is not None:
        query = query.where(Telemetry.device_id == device_id)
    if property_identifier:
        query = query.where(Telemetry.property_identifier == property_identifier)
    if start_time:
        query = query.where(Telemetry.timestamp >= start_time)
    if end_time:
        query = query.where(Telemetry.timestamp <= end_time)

    query = query.order_by(desc(Telemetry.timestamp)).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    return {
        "items": items,
        "skip": skip,
        "limit": limit,
        "total": len(items),
    }


@router.get("/devices/{device_id}", response_model=Dict[str, Any])
async def list_device_telemetry(
    device_id: int,
    property_identifier: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取某设备的遥测数据"""
    device_result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.owner_id == current_user.id,
        )
    )
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    query = select(Telemetry).where(Telemetry.device_id == device_id)
    if property_identifier:
        query = query.where(Telemetry.property_identifier == property_identifier)
    if start_time:
        query = query.where(Telemetry.timestamp >= start_time)
    if end_time:
        query = query.where(Telemetry.timestamp <= end_time)

    query = query.order_by(desc(Telemetry.timestamp)).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    return {
        "items": items,
        "skip": skip,
        "limit": limit,
        "total": len(items),
    }


@router.post("/", response_model=TelemetryResponse)
async def submit_telemetry(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """手动提交遥测点（用于测试）"""
    device_id = payload.get("device_id")
    prop_id = payload.get("property_identifier")
    value = payload.get("value")
    if device_id is None or prop_id is None or value is None:
        raise HTTPException(
            status_code=400,
            detail="device_id, property_identifier, and value are required",
        )

    device_result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.owner_id == current_user.id,
        )
    )
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    ts = payload.get("timestamp")
    if isinstance(ts, str):
        try:
            ts = datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            ts = datetime.utcnow()
    if not ts:
        ts = datetime.utcnow()

    db_telemetry = Telemetry(
        device_id=device_id,
        property_identifier=prop_id,
        value=str(value),
        timestamp=ts,
        quality=payload.get("quality", "good"),
    )
    db.add(db_telemetry)
    await db.commit()
    await db.refresh(db_telemetry)
    return db_telemetry
