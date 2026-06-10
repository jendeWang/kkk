from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime
import uuid
import json

from .deps import get_current_active_user, get_db
from ..models.models import Command, Device, User, CommandStatus
from ..schemas import CommandCreate, CommandResponse
from ..mqtt.service import mqtt_service

router = APIRouter(prefix="/commands", tags=["命令管理"])


@router.get("/", response_model=List[CommandResponse])
async def list_commands(
    device_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """列出命令（支持按设备或状态过滤）"""
    query = select(Command).join(Device).where(Device.owner_id == current_user.id)
    if device_id is not None:
        query = query.where(Command.device_id == device_id)
    if status:
        query = query.where(Command.status == status)
    query = query.order_by(desc(Command.created_at)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{command_id}", response_model=CommandResponse)
async def get_command(
    command_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取命令详情"""
    result = await db.execute(
        select(Command).join(Device).where(
            Command.command_id == command_id,
            Device.owner_id == current_user.id,
        )
    )
    command = result.scalar_one_or_none()
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")
    return command


@router.post("/", response_model=CommandResponse)
async def create_command(
    command: CommandCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建命令并通过 MQTT 下发到设备"""
    device_result = await db.execute(
        select(Device).where(
            Device.id == command.device_id,
            Device.owner_id == current_user.id,
        )
    )
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    command_id = f"cmd-{uuid.uuid4()}"
    db_command = Command(
        command_id=command_id,
        device_id=command.device_id,
        service_identifier=command.service_identifier,
        input_params=command.input_params,
        status=CommandStatus.PENDING,
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(db_command)
    await db.flush()

    if mqtt_service and getattr(mqtt_service, '_connected', False):
        try:
            topic = f"devices/{device.device_key}/commands"
            payload = {
                "command_id": command_id,
                "service_identifier": command.service_identifier,
                "input_params": command.input_params,
                "timestamp": datetime.utcnow().isoformat(),
            }
            mqtt_service.client.publish(topic, json.dumps(payload))
            db_command.status = CommandStatus.SENT
            db_command.sent_at = datetime.utcnow()
        except Exception as e:
            print(f"MQTT publish error: {e}")

    await db.commit()
    await db.refresh(db_command)
    return db_command


@router.delete("/{command_id}")
async def delete_command(
    command_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除命令"""
    result = await db.execute(
        select(Command).join(Device).where(
            Command.command_id == command_id,
            Device.owner_id == current_user.id,
        )
    )
    command = result.scalar_one_or_none()
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")
    await db.delete(command)
    await db.commit()
    return {"message": "Command deleted successfully"}
