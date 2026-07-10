import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.models import (
    AlertRule, AlertEvent, AlertType, AlertStatus, AlertSeverity,
    ConditionOperator, Device, AutomationScene, Telemetry
)

logger = logging.getLogger(__name__)


class AlertEngine:
    def __init__(self):
        self._rules_cache: Dict[int, AlertRule] = {}
        self._last_triggered: Dict[int, datetime] = {}
        self._notification_handlers = {}

    def register_notification_handler(self, name: str, handler):
        self._notification_handlers[name] = handler

    async def load_rules(self, db: AsyncSession, user_id: int):
        result = await db.execute(
            select(AlertRule).where(AlertRule.owner_id == user_id, AlertRule.enabled == True)
        )
        rules = result.scalars().all()
        self._rules_cache = {rule.id: rule for rule in rules}
        logger.info(f"Loaded {len(rules)} alert rules")

    async def evaluate_rule(
        self,
        db: AsyncSession,
        rule: AlertRule,
        device_id: int,
        property_identifier: str,
        value: Any,
        timestamp: Optional[datetime] = None
    ) -> Optional[AlertEvent]:
        if not rule.enabled:
            return None

        if rule.cooldown_seconds:
            last_time = self._last_triggered.get(rule.id)
            if last_time and (timestamp or datetime.utcnow()) - last_time < timedelta(seconds=rule.cooldown_seconds):
                logger.debug(f"Rule {rule.id} on cooldown, skipping")
                return None

        if rule.silent_from_hour is not None and rule.silent_to_hour is not None:
            now = (timestamp or datetime.utcnow()).hour
            if rule.silent_from_hour <= now < rule.silent_to_hour:
                logger.debug(f"Rule {rule.id} in silent period, skipping")
                return None

        if rule.alert_type == AlertType.THRESHOLD:
            return await self._evaluate_threshold_rule(db, rule, device_id, property_identifier, value, timestamp)

        return None

    async def _evaluate_threshold_rule(
        self,
        db: AsyncSession,
        rule: AlertRule,
        device_id: int,
        property_identifier: str,
        value: Any,
        timestamp: Optional[datetime] = None
    ) -> Optional[AlertEvent]:
        if rule.property_identifier and rule.property_identifier != property_identifier:
            return None

        if rule.device_id and rule.device_id != device_id:
            return None

        try:
            threshold = float(rule.threshold_value)
            current_value = float(value)
        except (ValueError, TypeError):
            logger.error(f"Cannot compare values: {value} vs {rule.threshold_value}")
            return None

        operator = rule.operator
        triggered = False

        if operator == ConditionOperator.GT:
            triggered = current_value > threshold
        elif operator == ConditionOperator.GTE:
            triggered = current_value >= threshold
        elif operator == ConditionOperator.LT:
            triggered = current_value < threshold
        elif operator == ConditionOperator.LTE:
            triggered = current_value <= threshold
        elif operator == ConditionOperator.EQ:
            triggered = abs(current_value - threshold) < 0.001
        elif operator == ConditionOperator.NEQ:
            triggered = abs(current_value - threshold) >= 0.001
        elif operator == ConditionOperator.INCREASE_RATE:
            triggered = await self._evaluate_rate_rule(db, rule, device_id, property_identifier, value, True)
        elif operator == ConditionOperator.DECREASE_RATE:
            triggered = await self._evaluate_rate_rule(db, rule, device_id, property_identifier, value, False)

        if triggered:
            if rule.duration_seconds:
                triggered = await self._check_duration(db, rule, device_id, property_identifier, rule.duration_seconds)

        if triggered:
            return await self._create_alert_event(db, rule, device_id, property_identifier, value, timestamp)

        return None

    async def _evaluate_rate_rule(
        self,
        db: AsyncSession,
        rule: AlertRule,
        device_id: int,
        property_identifier: str,
        value: Any,
        is_increase: bool
    ) -> bool:
        minutes = 5
        time_ago = datetime.utcnow() - timedelta(minutes=minutes)

        result = await db.execute(
            select(Telemetry)
            .where(
                Telemetry.device_id == device_id,
                Telemetry.property_identifier == property_identifier,
                Telemetry.timestamp >= time_ago
            )
            .order_by(Telemetry.timestamp)
            .limit(1)
        )
        old_record = result.scalar_one_or_none()
        if not old_record:
            return False

        try:
            old_value = float(old_record.value)
            current_value = float(value)
            rate = (current_value - old_value) / minutes
            threshold = float(rule.threshold_value)
            if is_increase:
                return rate > threshold
            else:
                return rate < -threshold
        except (ValueError, TypeError):
            return False

    async def _check_duration(
        self,
        db: AsyncSession,
        rule: AlertRule,
        device_id: int,
        property_identifier: str,
        duration_seconds: int
    ) -> bool:
        time_ago = datetime.utcnow() - timedelta(seconds=duration_seconds)

        result = await db.execute(
            select(Telemetry)
            .where(
                Telemetry.device_id == device_id,
                Telemetry.property_identifier == property_identifier,
                Telemetry.timestamp >= time_ago
            )
            .order_by(Telemetry.timestamp.desc())
            .limit(5)
        )
        records = result.scalars().all()
        if len(records) < 3:
            return False

        try:
            threshold = float(rule.threshold_value)
            operator = rule.operator
            count = 0
            for record in records:
                val = float(record.value)
                if operator == ConditionOperator.GT and val > threshold:
                    count += 1
                elif operator == ConditionOperator.GTE and val >= threshold:
                    count += 1
                elif operator == ConditionOperator.LT and val < threshold:
                    count += 1
                elif operator == ConditionOperator.LTE and val <= threshold:
                    count += 1
            return count >= len(records) * 0.8
        except (ValueError, TypeError):
            return False

    async def _create_alert_event(
        self,
        db: AsyncSession,
        rule: AlertRule,
        device_id: int,
        property_identifier: str,
        value: Any,
        timestamp: Optional[datetime] = None
    ) -> AlertEvent:
        event = AlertEvent(
            rule_id=rule.id,
            product_id=rule.product_id,
            device_id=device_id,
            property_identifier=property_identifier,
            message=f"{rule.name}: {property_identifier} {rule.operator.value} {rule.threshold_value}",
            severity=rule.severity,
            current_value=str(value),
            threshold_value=rule.threshold_value,
            operator=rule.operator.value,
            status=AlertStatus.TRIGGERED,
            created_at=timestamp or datetime.utcnow(),
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)

        self._last_triggered[rule.id] = event.created_at
        rule.last_triggered_at = event.created_at
        await db.commit()

        await self._send_notifications(rule, event)

        if rule.auto_execute_scene and rule.linked_scene_id:
            await self._execute_linked_scene(db, rule.linked_scene_id, device_id)

        logger.info(f"Alert event created: {event.id} - {event.message}")
        return event

    async def _send_notifications(self, rule: AlertRule, event: AlertEvent):
        if not rule.notification_config:
            return

        config = rule.notification_config
        if isinstance(config, str):
            import json
            try:
                config = json.loads(config)
            except json.JSONDecodeError:
                return

        for method, settings in config.items():
            handler = self._notification_handlers.get(method)
            if handler:
                try:
                    await handler(event, settings)
                except Exception as e:
                    logger.error(f"Notification {method} failed: {e}")

    async def _execute_linked_scene(self, db: AsyncSession, scene_id: int, device_id: int):
        from ..services.scene_service import SceneExecutor
        executor = SceneExecutor()
        await executor.execute_scene(db, scene_id, device_id)
        logger.info(f"Linked scene {scene_id} executed for device {device_id}")

    async def process_telemetry(
        self,
        db: AsyncSession,
        device_id: int,
        property_identifier: str,
        value: Any,
        timestamp: Optional[datetime] = None
    ):
        for rule in self._rules_cache.values():
            if rule.alert_type == AlertType.THRESHOLD:
                if rule.property_identifier and rule.property_identifier != property_identifier:
                    continue
                if rule.device_id and rule.device_id != device_id:
                    continue
                await self.evaluate_rule(db, rule, device_id, property_identifier, value, timestamp)

    async def check_device_offline(self, db: AsyncSession, device: Device):
        rules = [r for r in self._rules_cache.values()
                 if r.alert_type == AlertType.DEVICE_OFFLINE and (r.device_id is None or r.device_id == device.id)]

        for rule in rules:
            last_seen = device.last_seen or device.created_at
            if datetime.utcnow() - last_seen > timedelta(seconds=rule.duration_seconds or 300):
                await self._create_alert_event(
                    db, rule, device.id, "status", "offline", datetime.utcnow()
                )


alert_engine = AlertEngine()