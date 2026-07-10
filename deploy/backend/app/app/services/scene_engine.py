import uuid
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.models import (
    AutomationScene, AutomationExecutionLog, Device, Command,
    CommandStatus, TriggerType, ActionType, ExecutionStatus, ConditionOperator
)
from ..mqtt.service import mqtt_service


class SceneEngine:
    def __init__(self):
        self._cooldowns = {}

    async def check_and_trigger(self, db: AsyncSession, device_id: int, property_identifier: str, value):
        try:
            float_val = float(value)
        except (ValueError, TypeError):
            return

        result = await db.execute(
            select(AutomationScene).where(
                AutomationScene.enabled == True,
                AutomationScene.trigger_type == TriggerType.THRESHOLD,
            )
        )
        scenes = result.scalars().all()

        for scene in scenes:
            if not scene.trigger_config or not isinstance(scene.trigger_config, dict):
                continue

            config = scene.trigger_config
            config_device_id = config.get("device_id")
            config_property = config.get("property_identifier")

            if config_device_id is not None and config_device_id != device_id:
                continue
            if config_property and config_property != property_identifier:
                continue

            operator = config.get("operator")
            threshold_value = config.get("threshold_value")

            if not operator or threshold_value is None:
                continue

            try:
                threshold = float(threshold_value)
            except (ValueError, TypeError):
                continue

            if self._check_threshold(float_val, operator, threshold):
                if self._check_cooldown(scene.id, scene.cooldown_seconds):
                    trigger_data = {
                        "device_id": device_id,
                        "property_identifier": property_identifier,
                        "value": value,
                        "operator": operator,
                        "threshold_value": threshold_value,
                    }
                    await self.execute_scene(db, scene, trigger_data)

    async def execute_scene(self, db: AsyncSession, scene: AutomationScene, trigger_data: dict):
        log = AutomationExecutionLog(
            scene_id=scene.id,
            trigger_type=scene.trigger_type,
            trigger_data=trigger_data,
            status=ExecutionStatus.EXECUTING,
        )
        db.add(log)
        await db.flush()

        try:
            result_data = {}

            if scene.action_type == ActionType.COMMAND:
                result_data = await self._execute_command_action(db, scene)
            elif scene.action_type == ActionType.ALERT:
                result_data = await self._execute_alert_action(db, scene)
            elif scene.action_type == ActionType.WEBHOOK:
                result_data = await self._execute_webhook_action(db, scene)

            log.status = ExecutionStatus.SUCCESS
            log.result_data = result_data
            scene.last_triggered_at = datetime.utcnow()

            await db.commit()
            await db.refresh(log)

        except Exception as e:
            log.status = ExecutionStatus.FAILED
            log.error_message = str(e)
            await db.commit()

        return log

    async def _execute_command_action(self, db: AsyncSession, scene: AutomationScene) -> dict:
        action_config = scene.action_config
        if not action_config:
            return {"message": "No action config"}

        commands_list = action_config if isinstance(action_config, list) else [action_config]
        executed_commands = []

        for cmd_config in commands_list:
            if not isinstance(cmd_config, dict):
                continue

            device_id = cmd_config.get("device_id")
            service_identifier = cmd_config.get("service_identifier")
            input_params = cmd_config.get("input_params", {})

            if not device_id or not service_identifier:
                continue

            device_result = await db.execute(select(Device).where(Device.id == device_id))
            device = device_result.scalar_one_or_none()
            if not device:
                continue

            command_id = f"cmd-{uuid.uuid4()}"
            db_command = Command(
                command_id=command_id,
                device_id=device_id,
                service_identifier=service_identifier,
                input_params=input_params,
                status=CommandStatus.PENDING,
                owner_id=scene.owner_id,
                created_at=datetime.utcnow(),
            )
            db.add(db_command)
            await db.flush()

            if mqtt_service and getattr(mqtt_service, '_connected', False):
                try:
                    topic = f"devices/{device.device_key}/commands"
                    payload = {
                        "command_id": command_id,
                        "service_identifier": service_identifier,
                        "input_params": input_params,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                    mqtt_service.client.publish(topic, json.dumps(payload))
                    db_command.status = CommandStatus.SENT
                    db_command.sent_at = datetime.utcnow()
                except Exception as e:
                    print(f"[SceneEngine] MQTT publish error: {e}")

            executed_commands.append({
                "command_id": command_id,
                "device_id": device_id,
                "service_identifier": service_identifier,
            })

        return {"executed_commands": executed_commands, "count": len(executed_commands)}

    async def _execute_alert_action(self, db: AsyncSession, scene: AutomationScene) -> dict:
        return {"message": "Alert action triggered", "scene_name": scene.name}

    async def _execute_webhook_action(self, db: AsyncSession, scene: AutomationScene) -> dict:
        return {"message": "Webhook action triggered", "scene_name": scene.name}

    def _check_threshold(self, value: float, operator: str, threshold: float) -> bool:
        op = operator.value if hasattr(operator, 'value') else operator
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

    def _check_cooldown(self, scene_id: int, cooldown_seconds: int) -> bool:
        now = datetime.utcnow()
        key = f"scene_{scene_id}"

        if key in self._cooldowns:
            last_time = self._cooldowns[key]
            if cooldown_seconds and (now - last_time).total_seconds() < cooldown_seconds:
                return False

        self._cooldowns[key] = now
        return True


scene_engine = SceneEngine()
