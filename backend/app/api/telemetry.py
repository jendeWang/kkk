from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, cast, Float
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import io
import csv

from .deps import get_current_active_user, get_db
from ..models.models import Telemetry, Device, User, ProductProperty, PropertyDataType
from ..schemas import TelemetryResponse

router = APIRouter(prefix="/telemetry", tags=["遥测数据"])


def _convert_value_by_type(value: str, data_type: Optional[str]) -> Any:
    if value is None:
        return None
    
    if data_type is None:
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except (ValueError, TypeError):
            return value
    
    try:
        if data_type == PropertyDataType.INT or data_type == "int":
            return int(float(value))
        elif data_type == PropertyDataType.FLOAT or data_type == "float":
            return float(value)
        elif data_type == PropertyDataType.BOOL or data_type == "bool":
            return str(value).lower() in ('true', '1', 'yes', 'on')
        else:
            return value
    except (ValueError, TypeError):
        return value


async def _get_property_data_types(db: AsyncSession, user_id: int) -> Dict[str, str]:
    result = await db.execute(
        select(ProductProperty.identifier, ProductProperty.data_type)
        .join(Device, Device.product_id == ProductProperty.product_id)
        .where(Device.owner_id == user_id)
        .distinct()
    )
    rows = result.all()
    return {identifier: data_type.value if hasattr(data_type, 'value') else data_type 
            for identifier, data_type in rows}


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
    
    type_map = await _get_property_data_types(db, current_user.id)
    for item in items_dict:
        prop_id = item.get('property_identifier')
        if prop_id and prop_id in type_map:
            item['value'] = _convert_value_by_type(str(item['value']), type_map[prop_id])
            item['data_type'] = type_map[prop_id]
    
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

    csv_content = output.getvalue()
    if isinstance(csv_content, str):
        csv_content = csv_content.encode('utf-8-sig')
    else:
        csv_content = '\ufeff'.encode('utf-8') + csv_content

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
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


# ========== 数据聚合与趋势查询 ==========

@router.get("/aggregation", response_model=Dict[str, Any])
async def get_telemetry_aggregation(
    device_id: Optional[int] = Query(None),
    property_identifier: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取遥测数据聚合统计（最小值、最大值、平均值、计数）"""
    query = select(
        Telemetry.property_identifier,
        func.min(cast(Telemetry.value, Float)).label('min_value'),
        func.max(cast(Telemetry.value, Float)).label('max_value'),
        func.avg(cast(Telemetry.value, Float)).label('avg_value'),
        func.count(Telemetry.id).label('count'),
    ).join(Device).where(Device.owner_id == current_user.id)

    if device_id is not None:
        query = query.where(Telemetry.device_id == device_id)
    if property_identifier:
        query = query.where(Telemetry.property_identifier == property_identifier)
    if start_time:
        query = query.where(Telemetry.timestamp >= start_time)
    if end_time:
        query = query.where(Telemetry.timestamp <= end_time)

    query = query.group_by(Telemetry.property_identifier)
    result = await db.execute(query)
    rows = result.all()

    type_map = await _get_property_data_types(db, current_user.id)
    aggregations = []
    for row in rows:
        prop_id = row[0]
        data_type = type_map.get(prop_id, "float")
        aggregations.append({
            "property_identifier": prop_id,
            "data_type": data_type,
            "min_value": _convert_value_by_type(str(row[1]), data_type) if row[1] else None,
            "max_value": _convert_value_by_type(str(row[2]), data_type) if row[2] else None,
            "avg_value": _convert_value_by_type(str(row[3]), data_type) if row[3] else None,
            "count": row[4],
        })

    return {
        "aggregations": aggregations,
        "start_time": start_time.isoformat() if start_time else None,
        "end_time": end_time.isoformat() if end_time else None,
    }


@router.get("/trend", response_model=Dict[str, Any])
async def get_telemetry_trend(
    device_id: Optional[int] = Query(None),
    property_identifier: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    interval: str = Query("1h", description="时间间隔: 1m, 5m, 15m, 30m, 1h, 6h, 1d"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取遥测数据趋势（按时间间隔分组聚合）"""
    interval_map = {
        "1m": timedelta(minutes=1),
        "5m": timedelta(minutes=5),
        "15m": timedelta(minutes=15),
        "30m": timedelta(minutes=30),
        "1h": timedelta(hours=1),
        "6h": timedelta(hours=6),
        "1d": timedelta(days=1),
    }
    
    delta = interval_map.get(interval, timedelta(hours=1))
    
    if end_time is None:
        end_time = datetime.utcnow()
    if start_time is None:
        start_time = end_time - timedelta(days=1)

    query = select(Telemetry).join(Device).where(Device.owner_id == current_user.id)

    if device_id is not None:
        query = query.where(Telemetry.device_id == device_id)
    if property_identifier:
        query = query.where(Telemetry.property_identifier == property_identifier)
    query = query.where(Telemetry.timestamp >= start_time).where(Telemetry.timestamp <= end_time)

    result = await db.execute(query.order_by(Telemetry.timestamp))
    items = result.scalars().all()

    type_map = await _get_property_data_types(db, current_user.id)
    
    grouped_data = {}
    for item in items:
        ts = item.timestamp
        bucket_time = ts - timedelta(
            minutes=ts.minute % delta.total_seconds() // 60,
            seconds=ts.second,
            microseconds=ts.microsecond
        )
        bucket_key = bucket_time.isoformat()
        
        prop_id = item.property_identifier
        if prop_id not in grouped_data:
            grouped_data[prop_id] = {}
        
        if bucket_key not in grouped_data[prop_id]:
            grouped_data[prop_id][bucket_key] = []
        
        value = float(item.value) if item.value else None
        if value is not None:
            grouped_data[prop_id][bucket_key].append(value)

    trends = {}
    for prop_id, buckets in grouped_data.items():
        data_type = type_map.get(prop_id, "float")
        trend_data = []
        sorted_buckets = sorted(buckets.items())
        
        for bucket_key, values in sorted_buckets:
            if values:
                trend_data.append({
                    "timestamp": bucket_key,
                    "min_value": _convert_value_by_type(str(min(values)), data_type),
                    "max_value": _convert_value_by_type(str(max(values)), data_type),
                    "avg_value": _convert_value_by_type(str(sum(values) / len(values)), data_type),
                    "count": len(values),
                })
        
        trends[prop_id] = trend_data

    return {
        "trends": trends,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "interval": interval,
    }


@router.get("/latest", response_model=Dict[str, Any])
async def get_latest_telemetry(
    device_id: Optional[int] = Query(None),
    property_identifier: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有设备/属性的最新遥测值"""
    subquery = (
        select(
            Telemetry.device_id,
            Telemetry.property_identifier,
            func.max(Telemetry.timestamp).label('latest_timestamp'),
        )
        .join(Device)
        .where(Device.owner_id == current_user.id)
    )
    
    if device_id is not None:
        subquery = subquery.where(Telemetry.device_id == device_id)
    if property_identifier:
        subquery = subquery.where(Telemetry.property_identifier == property_identifier)
    
    subquery = subquery.group_by(Telemetry.device_id, Telemetry.property_identifier).subquery()

    query = (
        select(Telemetry)
        .join(subquery, (Telemetry.device_id == subquery.c.device_id) & 
                        (Telemetry.property_identifier == subquery.c.property_identifier) & 
                        (Telemetry.timestamp == subquery.c.latest_timestamp))
    )

    result = await db.execute(query)
    items = result.scalars().all()

    type_map = await _get_property_data_types(db, current_user.id)
    latest_values = []
    for item in items:
        prop_id = item.property_identifier
        data_type = type_map.get(prop_id, "float")
        latest_values.append({
            "device_id": item.device_id,
            "property_identifier": prop_id,
            "value": _convert_value_by_type(str(item.value), data_type),
            "data_type": data_type,
            "timestamp": item.timestamp.isoformat(),
            "quality": item.quality,
        })

    device_names = {}
    device_result = await db.execute(
        select(Device.id, Device.device_name).where(Device.owner_id == current_user.id)
    )
    for row in device_result.all():
        device_names[row[0]] = row[1]
    
    for value in latest_values:
        value["device_name"] = device_names.get(value["device_id"], str(value["device_id"]))

    return {
        "latest_values": latest_values,
        "count": len(latest_values),
    }


@router.get("/stats", response_model=Dict[str, Any])
async def get_telemetry_stats(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取遥测数据统计概览"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    total_count_result = await db.execute(
        select(func.count(Telemetry.id))
        .join(Device)
        .where(Device.owner_id == current_user.id)
        .where(Telemetry.timestamp >= start_time)
    )
    total_count = total_count_result.scalar() or 0

    property_count_result = await db.execute(
        select(func.count(func.distinct(Telemetry.property_identifier)))
        .join(Device)
        .where(Device.owner_id == current_user.id)
    )
    property_count = property_count_result.scalar() or 0

    device_count_result = await db.execute(
        select(func.count(func.distinct(Telemetry.device_id)))
        .join(Device)
        .where(Device.owner_id == current_user.id)
    )
    device_count = device_count_result.scalar() or 0

    daily_counts = []
    for i in range(days):
        day_start = end_time - timedelta(days=days - i)
        day_end = day_start + timedelta(days=1)
        
        day_result = await db.execute(
            select(func.count(Telemetry.id))
            .join(Device)
            .where(Device.owner_id == current_user.id)
            .where(Telemetry.timestamp >= day_start)
            .where(Telemetry.timestamp < day_end)
        )
        count = day_result.scalar() or 0
        daily_counts.append({
            "date": day_start.strftime('%Y-%m-%d'),
            "count": count,
        })

    return {
        "total_count": total_count,
        "property_count": property_count,
        "device_count": device_count,
        "days": days,
        "daily_counts": daily_counts,
    }