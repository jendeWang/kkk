import json
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.models import Device, Telemetry, Command, DeviceEventRecord, DeviceStatus, CommandStatus, AlertEvent, AlertType, AlertStatus, AlertSeverity
from ..services.sse_service import sse_service
from ..services.alert_service import alert_engine


class MQTTHandler:
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory

    async def verify_device(self, device_key: str, device_secret: str) -> Optional[Device]:
        async with self.db_session_factory() as db:
            result = await db.execute(
                select(Device).where(
                    Device.device_key == device_key,
                    Device.device_secret == device_secret,
                )
            )
            return result.scalar_one_or_none()

    async def handle_telemetry(self, device_key: str, payload: dict):
        """处理遥测数据上报"""
        device_secret = payload.pop("device_secret", None)
        device = await self.verify_device(device_key, device_secret) if device_secret else None

        # 如果验证失败或未传入 device_secret，尝试仅通过 device_key 查询
        if not device:
            async with self.db_session_factory() as db:
                result = await db.execute(select(Device).where(Device.device_key == device_key))
                device = result.scalar_one_or_none()

        if not device:
            print(f"[MQTT] Device verification failed for key: {device_key}")
            return

        async with self.db_session_factory() as db:
            # 在当前 session 中重新获取设备
            result = await db.execute(select(Device).where(Device.id == device.id))
            db_device = result.scalar_one_or_none()
            
            if not db_device:
                print(f"[MQTT] Device not found in database: {device_key}")
                return

            telemetry = Telemetry(
                device_id=db_device.id,
                property_identifier=payload.get("property_identifier"),
                value=str(payload.get("value")),
                timestamp=datetime.fromisoformat(payload.get("timestamp")) if payload.get("timestamp") else datetime.utcnow(),
                quality=payload.get("quality", "good"),
            )
            db.add(telemetry)
            try:
                db_device.status = DeviceStatus.ONLINE
            except (ValueError, TypeError):
                db_device.status = DeviceStatus.ONLINE
            db_device.last_seen = datetime.utcnow()
            await db.commit()
            await alert_engine.check_telemetry_alert(
                db, db_device.id, payload.get("property_identifier"), payload.get("value")
            )
            await sse_service.publish_device_status({
                "device_key": device_key,
                "device_name": db_device.device_name,
                "status": "online",
                "property_identifier": payload.get("property_identifier"),
                "value": str(payload.get("value")),
            })

    async def handle_status(self, device_key: str, payload: dict):
        device_secret = payload.pop("device_secret", None)
        device = await self.verify_device(device_key, device_secret) if device_secret else None
        if not device:
            print(f"[MQTT] Device verification failed for key: {device_key}")
            return

        async with self.db_session_factory() as db:
            new_status = payload.get("status", "offline")
            try:
                device.status = DeviceStatus(new_status)
            except ValueError:
                device.status = DeviceStatus.OFFLINE
            device.last_seen = datetime.utcnow()
            device.status_changed_at = datetime.utcnow()
            await db.commit()
            await sse_service.publish_device_status({
                "device_key": device_key,
                "device_name": device.device_name,
                "status": new_status,
            })

    async def handle_event(self, device_key: str, payload: dict):
        device_secret = payload.pop("device_secret", None)
        device = await self.verify_device(device_key, device_secret) if device_secret else None
        if not device:
            print(f"[MQTT] Device verification failed for key: {device_key}")
            return

        async with self.db_session_factory() as db:
            ts = payload.get("timestamp")
            if isinstance(ts, str):
                try:
                    ts = datetime.fromisoformat(ts)
                except (ValueError, TypeError):
                    ts = datetime.utcnow()
            else:
                ts = datetime.utcnow()
            event_record = DeviceEventRecord(
                device_id=device.id,
                event_identifier=payload.get("event_identifier"),
                event_data=payload.get("event_data"),
                timestamp=ts,
            )
            db.add(event_record)
            await db.commit()

    async def handle_command_response(self, device_key: str, payload: dict):
        print(f"[MQTT] Received command response for device {device_key}: {payload}")
        
        device_secret = payload.pop("device_secret", None)
        device = await self.verify_device(device_key, device_secret) if device_secret else None

        # 如果验证失败或未传入 device_secret，尝试仅通过 device_key 查询
        if not device:
            async with self.db_session_factory() as db:
                result = await db.execute(select(Device).where(Device.device_key == device_key))
                device = result.scalar_one_or_none()

        if not device:
            print(f"[MQTT] Device verification failed for key: {device_key}")
            return

        command_id = payload.get("command_id")
        if not command_id:
            print(f"[MQTT] Command response missing command_id")
            return

        async with self.db_session_factory() as db:
            result = await db.execute(select(Command).where(Command.command_id == command_id))
            command = result.scalar_one_or_none()
            if command:
                status = payload.get("status")
                if status == "executed":
                    command.status = CommandStatus.EXECUTED
                elif status == "failed":
                    command.status = CommandStatus.FAILED
                command.executed_at = datetime.utcnow()
                command.output_data = payload.get("output_data")
                command.error_message = payload.get("error_message")
                await db.commit()
                print(f"[MQTT] Command {command_id} updated to {status}")
            else:
                print(f"[MQTT] Command {command_id} not found")
