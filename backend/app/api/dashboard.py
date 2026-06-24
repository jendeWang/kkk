from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from typing import Optional
from datetime import datetime, timedelta

from .deps import get_current_active_user, get_db
from ..models.models import (
    User, Device, Product, Telemetry, AlertEvent, AlertSeverity, AlertStatus, DeviceShadow
)

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


@router.get("/overview")
async def get_dashboard_overview(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """仪表盘概览统计"""
    product_result = await db.execute(
        select(func.count(Product.id)).where(Product.owner_id == current_user.id)
    )
    total_products = product_result.scalar() or 0

    device_result = await db.execute(
        select(func.count(Device.id)).where(Device.owner_id == current_user.id)
    )
    total_devices = device_result.scalar() or 0

    online_result = await db.execute(
        select(func.count(Device.id)).where(
            Device.owner_id == current_user.id,
            Device.status == "online"
        )
    )
    online_devices = online_result.scalar() or 0

    alert_result = await db.execute(
        select(func.count(AlertEvent.id)).join(Device).where(
            Device.owner_id == current_user.id,
            AlertEvent.status == AlertStatus.TRIGGERED
        )
    )
    active_alerts = alert_result.scalar() or 0

    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_alert_result = await db.execute(
        select(func.count(AlertEvent.id)).join(Device).where(
            Device.owner_id == current_user.id,
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
    }


@router.get("/devices/realtime")
async def get_devices_realtime(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取所有设备的最新状态（设备影子）"""
    result = await db.execute(
        select(Device, DeviceShadow).outerjoin(
            DeviceShadow, Device.id == DeviceShadow.device_id
        ).where(Device.owner_id == current_user.id)
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

    return {"devices": devices}


@router.get("/alerts/summary")
async def get_alerts_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """告警统计摘要"""
    severities = ["critical", "error", "warning", "info"]
    result = {}

    for sev in severities:
        count_result = await db.execute(
            select(func.count(AlertEvent.id)).join(Device).where(
                Device.owner_id == current_user.id,
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
            Device.owner_id == current_user.id,
            AlertEvent.created_at >= today_start
        )
    )
    result["today_total"] = today_total.scalar() or 0

    last_7d_total = await db.execute(
        select(func.count(AlertEvent.id)).join(Device).where(
            Device.owner_id == current_user.id,
            AlertEvent.created_at >= last_7d_start
        )
    )
    result["last_7d_total"] = last_7d_total.scalar() or 0

    return result


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
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """最近告警事件"""
    query = select(AlertEvent, Device).join(
        Device, AlertEvent.device_id == Device.id
    ).where(
        Device.owner_id == current_user.id
    ).order_by(desc(AlertEvent.created_at)).limit(limit)

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

    return {"alerts": alerts}
