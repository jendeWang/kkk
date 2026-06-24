from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime
import io
import csv

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
    query = select(Telemetry).join(Device).where(Device.owner_id == current_user.id)
    count_query = select(func.count(Telemetry.id)).join(Device).where(Device.owner_id == current_user.id)

    if device_id is not None:
        query = query.where(Telemetry.device_id == device_id)
        count_query = count_query.where(Telemetry.device_id == device_id)
    if property_identifier:
        query = query.where(Telemetry.property_identifier == property_identifier)
        count_query = count_query.where(Telemetry.property_identifier == property_identifier)
    if start_time:
        query = query.where(Telemetry.timestamp >= start_time)
        count_query = count_query.where(Telemetry.timestamp >= start_time)
    if end_time:
        query = query.where(Telemetry.timestamp <= end_time)
        count_query = count_query.where(Telemetry.timestamp <= end_time)

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(desc(Telemetry.timestamp)).offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()
    items_dict = [TelemetryResponse.model_validate(item).model_dump() for item in items]
    return {
        "items": items_dict,
        "skip": skip,
        "limit": limit,
        "total": total,
    }


@router.get("/export/csv")
async def export_telemetry_csv(
    device_id: Optional[int] = Query(None),
    property_identifier: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Telemetry).join(Device).where(Device.owner_id == current_user.id)

    if device_id is not None:
        query = query.where(Telemetry.device_id == device_id)
    if property_identifier:
        query = query.where(Telemetry.property_identifier == property_identifier)
    if start_time:
        query = query.where(Telemetry.timestamp >= start_time)
    if end_time:
        query = query.where(Telemetry.timestamp <= end_time)

    query = query.order_by(desc(Telemetry.timestamp)).limit(10000)
    result = await db.execute(query)
    items = result.scalars().all()

    device_map = {}
    if device_id is None:
        device_result = await db.execute(
            select(Device).where(Device.owner_id == current_user.id)
        )
        devices = device_result.scalars().all()
        device_map = {d.id: d.device_name for d in devices}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['时间', '设备', '属性', '值', '质量'])

    for item in items:
        device_name = device_map.get(item.device_id, str(item.device_id))
        writer.writerow([
            item.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            device_name,
            item.property_identifier,
            item.value,
            item.quality
        ])

    output.seek(0)
    filename = f"telemetry_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


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
    items_dict = [TelemetryResponse.model_validate(item).model_dump() for item in items]
    return {
        "items": items_dict,
        "skip": skip,
        "limit": limit,
        "total": len(items_dict),
    }


@router.post("/", response_model=TelemetryResponse)
async def submit_telemetry(
    payload: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
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
