from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
import uuid
from .deps import get_current_active_user
from ..database import get_db
from ..models.models import User, Device, Command, CommandStatusEnum
from ..schemas import CommandCreate, CommandResponse
from ..mqtt.service import mqtt_service

router = APIRouter(prefix="/commands", tags=["命令管理"])


@router.post("/", response_model=CommandResponse)
async def create_command(
    command: CommandCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """下发命令"""
    # 验证设备存在且属于当前用户
    result = await db.execute(
        select(Device).where(
            Device.id == command.device_id,
            Device.owner_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    command_id = f"cmd-{uuid.uuid4()}"
    db_command = Command(
        command_id=command_id,
        device_id=command.device_id,
        service_identifier=command.service_identifier,
        parameters=command.parameters,
        status=CommandStatusEnum.PENDING,
        issued_at=datetime.utcnow()
    )
    db.add(db_command)
    await db.commit()
    await db.refresh(db_command)

    # 通过MQTT发布命令到设备
    await mqtt_service.publish_command(
        device.device_key,
        command_id,
        command.service_identifier,
        command.parameters
    )

    return db_command


@router.get("/", response_model=List[CommandResponse])
async def list_commands(
    device_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取命令列表"""
    query = select(Command).join(Device).where(Device.owner_id == current_user.id)

    if device_id:
        query = query.where(Command.device_id == device_id)
    if status:
        query = query.where(Command.status == status)

    query = query.order_by(Command.issued_at.desc()).limit(limit)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{command_id}", response_model=CommandResponse)
async def get_command(
    command_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取命令详情"""
    result = await db.execute(
        select(Command)
        .join(Device)
        .where(
            Command.command_id == command_id,
            Device.owner_id == current_user.id
        )
    )
    command = result.scalar_one_or_none()
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")
    return command
