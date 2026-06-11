import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.models import AlertRule, AlertEvent, Device, Telemetry, AlertType, AlertStatus, ConditionOperator, AlertSeverity
from .sse_service import sse_service


class AlertEngine:
    def __init__(self):
        self._cooldowns = {}

    async def check_telemetry_alert(self, db: AsyncSession, device_id: int, property_identifier: str, value):
        """检查遥测值是否触发阈值告警"""
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
        
        print(f"[AlertEngine] Checking telemetry: device_id={device_id}, property={property_identifier}, value={float_val}")
        print(f"[AlertEngine] Found {len(rules)} matching rules")
        for rule in rules:
            print(f"[AlertEngine] Rule: {rule.name}, threshold={rule.threshold_value}, operator={rule.operator}")

        for rule in rules:
            if self._check_threshold(float_val, rule):
                print(f"[AlertEngine] Threshold matched! Creating alert for rule {rule.name}")
                if self._should_trigger(rule, device_id):
                    await self._create_alert(db, rule, device_id, str(float_val))

    async def check_device_status_alert(self, db: AsyncSession, device_id: int, old_status, new_status):
        """检查设备状态变更是否触发告警"""
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
            message=f"{device.device_name}: 属性 {rule.property_identifier} 达到 {current_value} (阈值 {rule.threshold_value})",
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
            "created_at": alert.created_at.isoformat() if alert.created_at else datetime.utcnow().isoformat(),
        })


alert_engine = AlertEngine()
