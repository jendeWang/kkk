from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from .deps import get_current_active_user
from ..core.database import get_db
from ..models.models import User, AlertRule, AlertEvent, Device, AlertType, AlertStatus, AlertSeverity, ConditionOperator
from ..schemas import AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse, AlertEventResponse, AlertEventStatusUpdate
from ..services.alert_engine import alert_engine

router = APIRouter(prefix="/alerts", tags=["告警管理"])


def _try_enum(enum_cls, value):
    if value is None:
        return None
    try:
        return enum_cls(value)
    except (ValueError, TypeError):
        return value


@router.get("/", response_model=List[AlertEventResponse])
async def list_alert_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    device_id: Optional[int] = Query(None),
    severity: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取告警历史列表（支持分页和筛选）"""
    query = select(AlertEvent).join(Device).where(Device.owner_id == current_user.id)
    if status:
        status_enum = _try_enum(AlertStatus, status)
        query = query.where(AlertEvent.status == status_enum)
    if device_id is not None:
        query = query.where(AlertEvent.device_id == device_id)
    if severity:
        severity_enum = _try_enum(AlertSeverity, severity)
        query = query.where(AlertEvent.severity == severity_enum)
    query = query.order_by(desc(AlertEvent.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule: AlertRuleCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建告警规则"""
    from sqlalchemy.orm import selectinload
    if rule.device_id:
        device_result = await db.execute(
            select(Device).where(
                Device.id == rule.device_id,
                Device.owner_id == current_user.id,
            )
        )
        if not device_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Device not found")

    if rule.linked_scene_id:
        from ..models.models import AutomationScene
        scene_result = await db.execute(
            select(AutomationScene).where(
                AutomationScene.id == rule.linked_scene_id,
                AutomationScene.owner_id == current_user.id,
            )
        )
        if not scene_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Linked scene not found")

    db_rule = AlertRule(
        name=rule.name,
        description=rule.description,
        alert_type=rule.alert_type,
        device_id=rule.device_id,
        property_identifier=rule.property_identifier,
        operator=rule.operator,
        threshold_value=rule.threshold_value,
        severity=rule.severity,
        duration_seconds=rule.duration_seconds,
        cooldown_seconds=rule.cooldown_seconds,
        silent_from_hour=rule.silent_from_hour,
        silent_to_hour=rule.silent_to_hour,
        notification_config=rule.notification_config,
        linked_scene_id=rule.linked_scene_id,
        auto_execute_scene=rule.auto_execute_scene,
        enabled=rule.enabled if rule.enabled is not None else True,
        owner_id=current_user.id,
    )
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)

    result = await db.execute(
        select(AlertRule)
        .options(selectinload(AlertRule.linked_scene))
        .where(AlertRule.id == db_rule.id)
    )
    rule_with_scene = result.scalar_one()
    rule_dict = {c.name: getattr(rule_with_scene, c.name) for c in rule_with_scene.__table__.columns}
    rule_dict["linked_scene_name"] = rule_with_scene.linked_scene.name if rule_with_scene.linked_scene else None
    return rule_dict


@router.get("/rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取告警规则列表"""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(AlertRule)
        .options(selectinload(AlertRule.linked_scene))
        .where(AlertRule.owner_id == current_user.id)
        .order_by(desc(AlertRule.created_at))
    )
    rules = result.scalars().all()
    response = []
    for rule in rules:
        rule_dict = {c.name: getattr(rule, c.name) for c in rule.__table__.columns}
        rule_dict["linked_scene_name"] = rule.linked_scene.name if rule.linked_scene else None
        response.append(rule_dict)
    return response


@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取告警规则详情"""
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(AlertRule)
        .options(selectinload(AlertRule.linked_scene))
        .where(
            AlertRule.id == rule_id,
            AlertRule.owner_id == current_user.id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    rule_dict = {c.name: getattr(rule, c.name) for c in rule.__table__.columns}
    rule_dict["linked_scene_name"] = rule.linked_scene.name if rule.linked_scene else None
    return rule_dict


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: int,
    rule: AlertRuleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新告警规则"""
    from sqlalchemy.orm import selectinload
    from ..models.models import AutomationScene
    result = await db.execute(
        select(AlertRule).where(
            AlertRule.id == rule_id,
            AlertRule.owner_id == current_user.id,
        )
    )
    db_rule = result.scalar_one_or_none()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    update_data = rule.model_dump(exclude_unset=True)

    if "linked_scene_id" in update_data and update_data["linked_scene_id"]:
        scene_result = await db.execute(
            select(AutomationScene).where(
                AutomationScene.id == update_data["linked_scene_id"],
                AutomationScene.owner_id == current_user.id,
            )
        )
        if not scene_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Linked scene not found")

    for field, value in update_data.items():
        setattr(db_rule, field, value)

    await db.commit()

    result = await db.execute(
        select(AlertRule)
        .options(selectinload(AlertRule.linked_scene))
        .where(AlertRule.id == rule_id)
    )
    rule_with_scene = result.scalar_one()
    rule_dict = {c.name: getattr(rule_with_scene, c.name) for c in rule_with_scene.__table__.columns}
    rule_dict["linked_scene_name"] = rule_with_scene.linked_scene.name if rule_with_scene.linked_scene else None
    return rule_dict


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除告警规则"""
    result = await db.execute(
        select(AlertRule).where(
            AlertRule.id == rule_id,
            AlertRule.owner_id == current_user.id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    await db.delete(rule)
    await db.commit()
    return {"message": "Alert rule deleted successfully"}


@router.get("/events", response_model=List[AlertEventResponse])
async def list_alert_events(
    status: Optional[str] = Query(None),
    device_id: Optional[int] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取告警事件列表"""
    query = select(AlertEvent).join(Device).where(Device.owner_id == current_user.id)
    if status:
        status_enum = _try_enum(AlertStatus, status)
        query = query.where(AlertEvent.status == status_enum)
    if device_id is not None:
        query = query.where(AlertEvent.device_id == device_id)
    if severity:
        severity_enum = _try_enum(AlertSeverity, severity)
        query = query.where(AlertEvent.severity == severity_enum)
    query = query.order_by(desc(AlertEvent.created_at)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/events/{event_id}/status", response_model=AlertEventResponse)
async def update_alert_event_status(
    event_id: int,
    status_update: AlertEventStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新告警事件状态（确认/解决/归档）"""
    result = await db.execute(
        select(AlertEvent).join(Device).where(
            AlertEvent.id == event_id,
            Device.owner_id == current_user.id,
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Alert event not found")

    status_enum = _try_enum(AlertStatus, status_update.status)
    event.status = status_enum
    if event.acknowledged_at is None:
        event.acknowledged_at = datetime.utcnow()
        event.acknowledged_by = current_user.id

    if status_enum in (AlertStatus.RESOLVED, AlertStatus.ARCHIVED):
        event.resolved_at = datetime.utcnow()
        event.resolved_by = current_user.id

    await db.commit()
    await db.refresh(event)
    return event


@router.get("/stats", response_model=Dict[str, Any])
async def get_alert_stats(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取告警统计信息"""
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    total_result = await db.execute(
        select(func.count(AlertEvent.id))
        .join(Device)
        .where(Device.owner_id == current_user.id, AlertEvent.created_at >= start_time)
    )
    total = total_result.scalar() or 0

    severity_result = await db.execute(
        select(AlertEvent.severity, func.count(AlertEvent.id))
        .join(Device)
        .where(Device.owner_id == current_user.id, AlertEvent.created_at >= start_time)
        .group_by(AlertEvent.severity)
    )
    severity_counts = {s.value: c for s, c in severity_result.all()}

    status_result = await db.execute(
        select(AlertEvent.status, func.count(AlertEvent.id))
        .join(Device)
        .where(Device.owner_id == current_user.id, AlertEvent.created_at >= start_time)
        .group_by(AlertEvent.status)
    )
    status_counts = {s.value: c for s, c in status_result.all()}

    daily_result = await db.execute(
        select(func.date(AlertEvent.created_at), func.count(AlertEvent.id))
        .join(Device)
        .where(Device.owner_id == current_user.id, AlertEvent.created_at >= start_time)
        .group_by(func.date(AlertEvent.created_at))
        .order_by(func.date(AlertEvent.created_at))
    )
    daily_data = [{"date": str(d), "count": c} for d, c in daily_result.all()]

    return {
        "total": total,
        "severity": severity_counts,
        "status": status_counts,
        "daily": daily_data,
        "period": f"{days}天",
    }


@router.post("/rules/{rule_id}/test")
async def test_alert_rule(
    rule_id: int,
    test_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """测试告警规则"""
    result = await db.execute(
        select(AlertRule).where(
            AlertRule.id == rule_id,
            AlertRule.owner_id == current_user.id,
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    device_id = test_data.get("device_id", rule.device_id)
    property_identifier = test_data.get("property_identifier", rule.property_identifier)
    value = test_data.get("value", 0)

    if not device_id:
        raise HTTPException(status_code=400, detail="device_id is required")
    if not property_identifier:
        raise HTTPException(status_code=400, detail="property_identifier is required")

    event = await alert_engine.evaluate_rule(db, rule, device_id, property_identifier, value)

    return {
        "triggered": event is not None,
        "rule_id": rule_id,
        "device_id": device_id,
        "property_identifier": property_identifier,
        "test_value": value,
        "threshold": rule.threshold_value,
        "operator": rule.operator.value,
        "event_id": event.id if event else None,
        "message": event.message if event else "Rule not triggered",
    }


@router.post("/rules/batch/enable")
async def batch_enable_rules(
    rule_ids: List[int],
    enabled: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """批量启用/禁用告警规则"""
    if not rule_ids:
        return {"message": "No rule IDs provided", "updated": 0}

    update_count = 0
    for rule_id in rule_ids:
        result = await db.execute(
            select(AlertRule).where(
                AlertRule.id == rule_id,
                AlertRule.owner_id == current_user.id,
            )
        )
        rule = result.scalar_one_or_none()
        if rule:
            rule.enabled = enabled
            update_count += 1

    await db.commit()
    return {"message": f"Updated {update_count} rules", "updated": update_count}
