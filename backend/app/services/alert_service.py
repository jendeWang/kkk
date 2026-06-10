import asyncio
from typing import Dict, List, Set
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from ..models.models import AlertRule, AlertEvent, Device, Telemetry
from .sse_service import sse_service


class AlertEngine:
    def __init__(self):
        self._cooldowns: Dict[int, datetime] = {}

    async def check_telemetry_alert(
        self,
        db: AsyncSession,
        device_id: int,
        property_identifier: str,
        value: float
    ):
        """检查遥测数据是否触发告警规则"""
        # 获取该设备对应的告警规则
        result = await db.execute(
            select(AlertRule).where(
                AlertRule.enabled == True,
                AlertRule.device_id.in_([device_id, None]),  # 匹配特定设备或所有设备
                AlertRule.property_identifier == property_identifier,
                AlertRule.alert_type == "threshold"
            )
        )
        rules = result.scalars().all()

        for rule in rules:
            if self._should_trigger(rule, device_id):
                await self._trigger_alert(db, rule, device_id, value)

    async def check_device_status_alert(
        self,
        db: AsyncSession,
        device_id: int,
        old_status: str,
        new_status: str
    ):
        """检查设备状态变更是否触发告警"""
        if old_status == "online" and new_status == "offline":
            result = await db.execute(
                select(AlertRule).where(
                    AlertRule.enabled == True,
                    AlertRule.device_id.in_([device_id, None]),
                    AlertRule.alert_type == "device_status"
                )
            )
            rules = result.scalars().all()

            for rule in rules:
                if self._should_trigger(rule, device_id):
                    await self._trigger_alert(db, rule, device_id, None)

    def _should_trigger(self, rule: AlertRule, device_id: int) -> bool:
        """检查规则是否应该触发"""
        # 检查冷却时间
        rule_key = f"{rule.id}_{device_id}"
        if rule_key in self._cooldowns:
            last_triggered = self._cooldowns[rule_key]
            if rule.cooldown_seconds:
                if (datetime.utcnow() - last_triggered).total_seconds() < rule.cooldown_seconds:
                    return False

        # 检查静默时段
        if rule.silent_from_hour is not None and rule.silent_to_hour is not None:
            current_hour = datetime.utcnow().hour
            if rule.silent_from_hour <= current_hour < rule.silent_to_hour:
                return False

        return True

    async def _trigger_alert(
        self,
        db: AsyncSession,
        rule: AlertRule,
        device_id: int,
        current_value: float = None
    ):
        """触发告警"""
        # 获取设备信息
        device_result = await db.execute(select(Device).where(Device.id == device_id))
        device = device_result.scalar_one_or_none()
        if not device:
            return

        # 构建告警消息
        if rule.alert_type == "threshold":
            message = f"设备 {device.device_name} 的属性 {rule.property_identifier} 超过阈值: {current_value} {rule.operator} {rule.threshold_value}"
        else:
            message = f"设备 {device.device_name} 已离线"

        # 创建告警事件
        alert_event = AlertEvent(
            rule_id=rule.id,
            device_id=device_id,
            message=message,
            severity=rule.severity,
            current_value=str(current_value) if current_value else None,
            threshold_value=rule.threshold_value,
            status="triggered"
        )
        db.add(alert_event)

        # 更新规则最后触发时间
        rule.last_triggered_at = datetime.utcnow()

        # 设置冷却时间
        rule_key = f"{rule.id}_{device_id}"
        self._cooldowns[rule_key] = datetime.utcnow()

        await db.commit()

        # 通过SSE推送到前端
        await sse_service.publish_alert({
            "id": alert_event.id,
            "message": message,
            "severity": rule.severity,
            "device_id": device_id,
            "device_name": device.device_name,
            "created_at": alert_event.created_at.isoformat() if alert_event.created_at else datetime.utcnow().isoformat()
        })


alert_engine = AlertEngine()
