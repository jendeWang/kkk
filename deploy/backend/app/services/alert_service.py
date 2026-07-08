import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ..models.models import AlertRule, AlertEvent, Device, Telemetry, AlertType, AlertStatus, ConditionOperator, AlertSeverity, AutomationScene
from .sse_service import sse_service
from .scene_engine import scene_engine


class AlertEngine:
    def __init__(self):
        self._cooldowns = {}
        self._duration_tracker = {}
        self._active_alerts = {}

    async def check_telemetry_alert(self, db: AsyncSession, device_id: int, property_identifier: str, value):
        try:
            float_val = float(value)
        except (ValueError, TypeError):
            return

        result = await db.execute(
            select(AlertRule).where(
                AlertRule.enabled == True,
                AlertRule.alert_type == AlertType.THRESHOLD,
                AlertRule.property_identifier == property_identifier,
                (AlertRule.device_id == device_id) | (AlertRule.device_id.is_(None)),
            )
        )
        rules = result.scalars().all()

        for rule in rules:
            await self._process_threshold_rule(db, rule, device_id, float_val)

    async def check_device_status_alert(self, db: AsyncSession, device_id: int, old_status, new_status):
        old_val = getattr(old_status, 'value', old_status) if old_status else None
        new_val = getattr(new_status, 'value', new_status) if new_status else None

        target_type = None
        if new_val == "offline":
            target_type = AlertType.DEVICE_OFFLINE
        elif new_val == "online":
            target_type = AlertType.DEVICE_ONLINE

        if target_type is None:
            return

        result = await db.execute(
            select(AlertRule).where(
                AlertRule.enabled == True,
                AlertRule.alert_type == target_type,
                AlertRule.device_id.in_([device_id, None]),
            )
        )
        rules = result.scalars().all()

        for rule in rules:
            if self._should_trigger(rule, device_id):
                await self._create_alert(db, rule, device_id, new_val)

    async def _process_threshold_rule(self, db: AsyncSession, rule: AlertRule, device_id: int, value: float):
        key = f"{rule.id}_{device_id}"
        threshold_met = self._check_threshold(value, rule)
        now = datetime.utcnow()

        if threshold_met:
            if rule.duration_seconds and rule.duration_seconds > 0:
                if key not in self._duration_tracker:
                    self._duration_tracker[key] = now
                    return
                elapsed = (now - self._duration_tracker[key]).total_seconds()
                if elapsed < rule.duration_seconds:
                    return
            else:
                self._duration_tracker[key] = now

            if key not in self._active_alerts or not self._active_alerts[key]:
                if self._should_trigger(rule, device_id):
                    await self._create_alert(db, rule, device_id, str(value))
                    self._active_alerts[key] = True
        else:
            if key in self._duration_tracker:
                del self._duration_tracker[key]

            if key in self._active_alerts and self._active_alerts[key]:
                await self._resolve_alert(db, rule, device_id, str(value))
                self._active_alerts[key] = False

    def _check_threshold(self, value: float, rule: AlertRule) -> bool:
        if rule.threshold_value is None or rule.operator is None:
            return False
        try:
            threshold = float(rule.threshold_value)
        except (ValueError, TypeError):
            return False

        op = rule.operator.value if hasattr(rule.operator, 'value') else rule.operator

        if op == "gt":
            return value > threshold
        elif op == "gte":
            return value >= threshold
        elif op == "lt":
            return value < threshold
        elif op == "lte":
            return value <= threshold
        elif op == "eq":
            return value == threshold
        elif op == "neq":
            return value != threshold
        return False

    def _should_trigger(self, rule: AlertRule, device_id: int) -> bool:
        key = f"{rule.id}_{device_id}"
        if key in self._cooldowns:
            last_time = self._cooldowns[key]
            if rule.cooldown_seconds and (datetime.utcnow() - last_time).total_seconds() < rule.cooldown_seconds:
                return False

        if rule.silent_from_hour is not None and rule.silent_to_hour is not None:
            hour = datetime.utcnow().hour
            if rule.silent_from_hour <= hour < rule.silent_to_hour:
                return False

        self._cooldowns[key] = datetime.utcnow()
        return True

    async def _create_alert(self, db: AsyncSession, rule: AlertRule, device_id: int, current_value: str):
        device_result = await db.execute(select(Device).where(Device.id == device_id))
        device = device_result.scalar_one_or_none()
        if not device:
            return

        severity_val = rule.severity.value if hasattr(rule.severity, 'value') else rule.severity

        alert = AlertEvent(
            rule_id=rule.id,
            device_id=device_id,
            property_identifier=rule.property_identifier,
            message=f"{device.device_name}: {rule.property_identifier} = {current_value}，超过阈值 {rule.threshold_value}",
            severity=rule.severity,
            current_value=str(current_value) if current_value is not None else None,
            threshold_value=rule.threshold_value,
            operator=rule.operator.value if hasattr(rule.operator, 'value') else rule.operator,
            status=AlertStatus.TRIGGERED,
        )
        db.add(alert)

        rule.last_triggered_at = datetime.utcnow()
        await db.commit()
        await db.refresh(alert)

        await sse_service.publish_alert({
            "id": alert.id,
            "message": alert.message,
            "severity": severity_val,
            "device_id": device_id,
            "device_name": device.device_name,
            "status": "triggered",
            "created_at": alert.created_at.isoformat() if alert.created_at else datetime.utcnow().isoformat(),
        })

        if rule.auto_execute_scene and rule.linked_scene_id:
            try:
                scene_result = await db.execute(
                    select(AutomationScene).where(
                        AutomationScene.id == rule.linked_scene_id,
                        AutomationScene.enabled == True,
                    )
                )
                scene = scene_result.scalar_one_or_none()
                if scene:
                    trigger_data = {
                        "trigger_type": "alert",
                        "alert_rule_id": rule.id,
                        "alert_event_id": alert.id,
                        "device_id": device_id,
                        "property_identifier": rule.property_identifier,
                        "value": current_value,
                    }
                    asyncio.create_task(scene_engine.execute_scene(db, scene, trigger_data))
            except Exception as e:
                print(f"[AlertEngine] Auto execute scene failed: {e}")

    async def _resolve_alert(self, db: AsyncSession, rule: AlertRule, device_id: int, current_value: str):
        device_result = await db.execute(select(Device).where(Device.id == device_id))
        device = device_result.scalar_one_or_none()
        if not device:
            return

        result = await db.execute(
            select(AlertEvent).where(
                AlertEvent.rule_id == rule.id,
                AlertEvent.device_id == device_id,
                AlertEvent.status == AlertStatus.TRIGGERED,
            ).order_by(AlertEvent.created_at.desc()).limit(1)
        )
        alert = result.scalar_one_or_none()

        if alert:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.resolution_notes = f"自动恢复: 当前值 {current_value}，已回到正常范围"
            await db.commit()

            severity_val = rule.severity.value if hasattr(rule.severity, 'value') else rule.severity
            await sse_service.publish_alert({
                "id": alert.id,
                "message": f"{device.device_name}: {rule.property_identifier} 已恢复正常 (当前值: {current_value})",
                "severity": severity_val,
                "device_id": device_id,
                "device_name": device.device_name,
                "status": "resolved",
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else datetime.utcnow().isoformat(),
            })


alert_engine = AlertEngine()
