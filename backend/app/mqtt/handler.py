import json
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.models import Device, Telemetry, Command, DeviceEventRecord, DeviceStatusEnum, CommandStatusEnum
from ..services.alert_service import alert_engine
from ..services.sse_service import sse_service


class MQTTHandler:
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory

    async def verify_device(self, device_key: str, device_secret: str) -> Optional[Device]:
        """验证设备密钥"""
        async with self.db_session_factory() as db:
            result = await db.execute(
                select(Device).where(
                    Device.device_key == device_key,
                    Device.device_secret == device_secret
                )
            )
            device = result.scalar_one_or_none()
            return device

    async def handle_telemetry(self, device_key: str, payload: dict):
        """处理遥测数据上报"""
        device_secret = payload.pop("device_secret", None)
        device = await self.verify_device(device_key, device_secret)
        if not device:
            print(f"Device verification failed for key: {device_key}")
            return

        async with self.db_session_factory() as db:
            # 创建遥测数据记录
            telemetry = Telemetry(
                device_id=device.id,
                property_identifier=payload.get("property_identifier"),
                value=str(payload.get("value")),
                timestamp=datetime.fromisoformat(payload.get("timestamp", datetime.utcnow().isoformat())),
                quality=payload.get("quality", "good")
            )
            db.add(telemetry)

            # 更新设备状态为在线
            old_status = device.status
            device.status = DeviceStatusEnum.ONLINE
            device.last_seen = datetime.utcnow()

            await db.commit()

            # 检查告警规则
            try:
                value = float(payload.get("value"))
                await alert_engine.check_telemetry_alert(
                    db, device.id, payload.get("property_identifier"), value
                )
            except (ValueError, TypeError):
                pass

            # 如果设备状态发生变化，推送SSE
            if old_status != DeviceStatusEnum.ONLINE:
                await sse_service.publish_device_status({
                    "device_key": device.device_key,
                    "device_name": device.device_name,
                    "status": "online"
                })

    async def handle_status(self, device_key: str, payload: dict):
        """处理设备状态上报"""
        device_secret = payload.pop("device_secret", None)
        device = await self.verify_device(device_key, device_secret)
        if not device:
            print(f"Device verification failed for key: {device_key}")
            return

        async with self.db_session_factory() as db:
            old_status = device.status
            new_status = payload.get("status", "online")
            device.status = DeviceStatusEnum(new_status)
            device.last_seen = datetime.utcnow()
            device.status_changed_at = datetime.utcnow()

            await db.commit()

            # 检查设备状态告警
            if old_status == DeviceStatusEnum.ONLINE and new_status == "offline":
                await alert_engine.check_device_status_alert(db, device.id, old_status, new_status)

            # 推送SSE
            await sse_service.publish_device_status({
                "device_key": device.device_key,
                "device_name": device.device_name,
                "status": new_status
            })

    async def handle_event(self, device_key: str, payload: dict):
        """处理设备事件上报"""
        device_secret = payload.pop("device_secret", None)
        device = await self.verify_device(device_key, device_secret)
        if not device:
            print(f"Device verification failed for key: {device_key}")
            return

        async with self.db_session_factory() as db:
            event_record = DeviceEventRecord(
                device_id=device.id,
                event_identifier=payload.get("event_identifier"),
                event_data=payload.get("event_data"),
                timestamp=datetime.fromisoformat(payload.get("timestamp", datetime.utcnow().isoformat()))
            )
            db.add(event_record)
            await db.commit()

    async def handle_command_response(self, device_key: str, payload: dict):
        """处理命令响应"""
        device_secret = payload.pop("device_secret", None)
        device = await self.verify_device(device_key, device_secret)
        if not device:
            print(f"Device verification failed for key: {device_key}")
            return

        command_id = payload.get("command_id")
        async with self.db_session_factory() as db:
            result = await db.execute(
                select(Command).where(Command.command_id == command_id)
            )
            command = result.scalar_one_or_none()
            if command:
                command.status = CommandStatusEnum(payload.get("status", "executed"))
                command.executed_at = datetime.fromisoformat(payload.get("timestamp", datetime.utcnow().isoformat()))
                command.output_data = payload.get("output_data")
                if payload.get("error_message"):
                    command.error_message = payload.get("error_message")
                await db.commit()
