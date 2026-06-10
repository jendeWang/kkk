from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from .deps import get_current_active_user
from ..database import get_db
from ..models.models import User, AlertRule, AlertEvent, Device
from ..schemas import (
    AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse,
    AlertEventResponse, AlertEventStatusUpdate
)

router = APIRouter(prefix="/alerts", tags=["告警管理"])


# Alert Rules
@router.post("/rules", response_model=AlertRuleResponse)
async def create_alert_rule(
    rule: AlertRuleCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建告警规则"""
    if rule.device_id:
        # 验证设备存在且属于当前用户
        result = await db.execute(
            select(Device).where(
                Device.id == rule.device_id,
                Device.owner_id == current_user.id
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Device not found")

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
        enabled=rule.enabled,
        owner_id=current_user.id
    )
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    return db_rule


@router.get("/rules", response_model=List[AlertRuleResponse])
async def list_alert_rules(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取告警规则列表"""
    result = await db.execute(
        select(AlertRule).where(AlertRule.owner_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/rules/{rule_id}", response_model=AlertRuleResponse)
async def get_alert_rule(
    rule_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取告警规则详情"""
    result = await db.execute(
        select(AlertRule).where(
            AlertRule.id == rule_id,
            AlertRule.owner_id == current_user.id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    return rule


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(
    rule_id: int,
    rule: AlertRuleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新告警规则"""
    result = await db.execute(
        select(AlertRule).where(
            AlertRule.id == rule_id,
            AlertRule.owner_id == current_user.id
        )
    )
    db_rule = result.scalar_one_or_none()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    for key, value in rule.model_dump(exclude_unset=True).items():
        setattr(db_rule, key, value)

    await db.commit()
    await db.refresh(db_rule)
    return db_rule


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(
    rule_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除告警规则"""
    result = await db.execute(
        select(AlertRule).where(
            AlertRule.id == rule_id,
            AlertRule.owner_id == current_user.id
        )
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    await db.delete(rule)
    await db.commit()
    return {"message": "Alert rule deleted successfully"}


# Alert Events
@router.get("/events", response_model=List[AlertEventResponse])
async def list_alert_events(
    status: Optional[str] = Query(None),
    device_id: Optional[int] = Query(None),
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取告警事件列表"""
    query = select(AlertEvent).join(Device).where(Device.owner_id == current_user.id)

    if status:
        query = query.where(AlertEvent.status == status)
    if device_id:
        query = query.where(AlertEvent.device_id == device_id)

    query = query.order_by(AlertEvent.created_at.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.put("/events/{event_id}/status", response_model=AlertEventResponse)
async def update_alert_event_status(
    event_id: int,
    status_update: AlertEventStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新告警事件状态"""
    result = await db.execute(
        select(AlertEvent)
        .join(Device)
        .where(
            AlertEvent.id == event_id,
            Device.owner_id == current_user.id
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Alert event not found")

    event.status = status_update.status
    if status_update.status == "acknowledged":
        event.acknowledged_at = datetime.utcnow()
    elif status_update.status == "resolved":
        event.resolved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(event)
    return event
