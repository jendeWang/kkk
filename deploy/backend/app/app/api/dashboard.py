from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from typing import Optional, List
from datetime import datetime, timedelta

from .deps import get_current_active_user, get_db
from ..models.models import (
    User, Device, Product, Telemetry, AlertEvent, AlertSeverity, AlertStatus, DeviceShadow,
    DeviceGroup, DeviceGroupMember
)

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


async def _get_group_device_ids(db: AsyncSession, current_user: User, group_id: int) -> List[int]:
    group_result = await db.execute(
        select(DeviceGroup).where(
            DeviceGroup.id == group_id,
            DeviceGroup.owner_id == current_user.id,
        )
    )
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    member_result = await db.execute(
        select(DeviceGroupMember.device_id).where(DeviceGroupMember.group_id == group_id)
    )
    return [row[0] for row in member_result.all()]


@router.get("/overview")
async def get_dashboard_overview(
    group_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """仪表盘概览统计（支持按大棚分组查询）"""
    device_ids = None
    if group_id:
        device_ids = await _get_group_device_ids(db, current_user, group_id)

    if device_ids is not None:
        device_filter = Device.id.in_(device_ids)
    else:
        device_filter = Device.owner_id == current_user.id

    product_result = await db.execute(
        select(func.count(Product.id)).where(Product.owner_id == current_user.id)
    )
    total_products = product_result.scalar() or 0

    device_result = await db.execute(
        select(func.count(Device.id)).where(device_filter)
    )
    total_devices = device_result.scalar() or 0

    online_result = await db.execute(
        select(func.count(Device.id)).where(
            device_filter,
            Device.status == "online"
        )
    )
    online_devices = online_result.scalar() or 0

    alert_result = await db.execute(
        select(func.count(AlertEvent.id)).join(Device).where(
            device_filter,
            AlertEvent.status == AlertStatus.TRIGGERED
        )
    )
    active_alerts = alert_result.scalar() or 0

    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_alert_result = await db.execute(
        select(func.count(AlertEvent.id)).join(Device).where(
            device_filter,
            AlertEvent.created_at >= today_start
        )
    )
    today_alerts = today_alert_result.scalar() or 0

    return {
        "total_products": total_products,
        "total_devices": total_devices,
        "online_devices": online_devices,
        "offline_devices": total_devices - online_devices,
        "active_alerts": active_alerts,
        "today_alerts": today_alerts,
        "group_id": group_id,
    }


@router.get("/devices/realtime")
async def get_devices_realtime(
    group_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取设备的最新状态（设备影子，支持按大棚分组查询）"""
    device_ids = None
    if group_id:
        device_ids = await _get_group_device_ids(db, current_user, group_id)

    if device_ids is not None:
        device_filter = Device.id.in_(device_ids)
    else:
        device_filter = Device.owner_id == current_user.id

    result = await db.execute(
        select(Device, DeviceShadow).outerjoin(
            DeviceShadow, Device.id == DeviceShadow.device_id
        ).where(device_filter)
    )
    rows = result.all()

    devices = []
    for device, shadow in rows:
        device_data = {
            "id": device.id,
            "device_name": device.device_name,
            "device_key": device.device_key,
            "product_id": device.product_id,
            "status": device.status,
            "last_seen": device.last_seen.isoformat() if device.last_seen else None,
            "reported": shadow.reported if shadow else {},
            "desired": shadow.desired if shadow else {},
        }
        devices.append(device_data)

    return {"devices": devices, "group_id": group_id}


@router.get("/alerts/summary")
async def get_alerts_summary(
    group_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """告警统计摘要（支持按大棚分组查询）"""
    device_ids = None
    if group_id:
        device_ids = await _get_group_device_ids(db, current_user, group_id)

    if device_ids is not None:
        device_filter = Device.id.in_(device_ids)
    else:
        device_filter = Device.owner_id == current_user.id

    severities = ["critical", "error", "warning", "info"]
    result = {}

    for sev in severities:
        count_result = await db.execute(
            select(func.count(AlertEvent.id)).join(Device).where(
                device_filter,
                AlertEvent.severity == sev,
                AlertEvent.status == AlertStatus.TRIGGERED
            )
        )
        result[f"{sev}_count"] = count_result.scalar() or 0

    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    last_7d_start = datetime.utcnow() - timedelta(days=7)

    today_total = await db.execute(
        select(func.count(AlertEvent.id)).join(Device).where(
            device_filter,
            AlertEvent.created_at >= today_start
        )
    )
    result["today_total"] = today_total.scalar() or 0

    last_7d_total = await db.execute(
        select(func.count(AlertEvent.id)).join(Device).where(
            device_filter,
            AlertEvent.created_at >= last_7d_start
        )
    )
    result["last_7d_total"] = last_7d_total.scalar() or 0

    return {**result, "group_id": group_id}


@router.get("/telemetry/trend")
async def get_telemetry_trend(
    device_id: int,
    property_identifier: str,
    hours: int = Query(6, ge=1, le=168),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取单个属性的历史趋势数据"""
    device_result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.owner_id == current_user.id,
        )
    )
    device = device_result.scalar_one_or_none()
    if not device:
        return {"data": []}

    start_time = datetime.utcnow() - timedelta(hours=hours)

    query = select(Telemetry).where(
        Telemetry.device_id == device_id,
        Telemetry.property_identifier == property_identifier,
        Telemetry.timestamp >= start_time
    ).order_by(Telemetry.timestamp.asc())

    result = await db.execute(query)
    items = result.scalars().all()

    data_points = []
    for item in items:
        try:
            val = float(item.value)
        except (ValueError, TypeError):
            val = item.value
        data_points.append({
            "timestamp": item.timestamp.isoformat(),
            "value": val
        })

    return {
        "device_id": device_id,
        "property_identifier": property_identifier,
        "data": data_points
    }


@router.get("/alerts/recent")
async def get_recent_alerts(
    limit: int = Query(10, ge=1, le=100),
    group_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """最近告警事件（支持按大棚分组查询）"""
    device_ids = None
    if group_id:
        device_ids = await _get_group_device_ids(db, current_user, group_id)

    if device_ids is not None:
        device_filter = Device.id.in_(device_ids)
    else:
        device_filter = Device.owner_id == current_user.id

    query = select(AlertEvent, Device).join(
        Device, AlertEvent.device_id == Device.id
    ).where(device_filter).order_by(desc(AlertEvent.created_at)).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    alerts = []
    for alert, device in rows:
        alerts.append({
            "id": alert.id,
            "message": alert.message,
            "severity": alert.severity,
            "status": alert.status,
            "device_id": device.id,
            "device_name": device.device_name,
            "property_identifier": alert.property_identifier,
            "current_value": alert.current_value,
            "threshold_value": alert.threshold_value,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
        })

    return {"alerts": alerts, "group_id": group_id}


@router.get("/greenhouses")
async def get_greenhouse_groups(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有大棚分组列表（用于仪表盘切换）"""
    query = select(DeviceGroup).where(DeviceGroup.owner_id == current_user.id)
    result = await db.execute(query)
    groups = result.scalars().all()

    group_ids = [g.id for g in groups]
    count_result = await db.execute(
        select(DeviceGroupMember.group_id, func.count(DeviceGroupMember.id))
        .where(DeviceGroupMember.group_id.in_(group_ids))
        .group_by(DeviceGroupMember.group_id)
    )
    device_counts = {row[0]: row[1] for row in count_result.all()}

    online_counts = {}
    if group_ids:
        online_result = await db.execute(
            select(DeviceGroupMember.group_id, func.count(Device.id))
            .join(Device, DeviceGroupMember.device_id == Device.id)
            .where(
                DeviceGroupMember.group_id.in_(group_ids),
                Device.status == "online"
            )
            .group_by(DeviceGroupMember.group_id)
        )
        online_counts = {row[0]: row[1] for row in online_result.all()}

    alert_counts = {}
    if group_ids:
        alert_result = await db.execute(
            select(DeviceGroupMember.group_id, func.count(AlertEvent.id))
            .join(Device, DeviceGroupMember.device_id == Device.id)
            .join(AlertEvent, AlertEvent.device_id == Device.id)
            .where(
                DeviceGroupMember.group_id.in_(group_ids),
                AlertEvent.status == AlertStatus.TRIGGERED
            )
            .group_by(DeviceGroupMember.group_id)
        )
        alert_counts = {row[0]: row[1] for row in alert_result.all()}

    greenhouse_list = []
    for g in groups:
        greenhouse_list.append({
            "id": g.id,
            "name": g.name,
            "description": g.description,
            "device_count": device_counts.get(g.id, 0),
            "online_count": online_counts.get(g.id, 0),
            "active_alerts": alert_counts.get(g.id, 0),
            "created_at": g.created_at.isoformat() if g.created_at else None,
        })

    return {"greenhouses": greenhouse_list}
