from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import random
import string
import json
import logging

from .deps import get_current_active_user, get_db
from ..models.models import User, Device, Product, ProductProperty, Command, Telemetry, DeviceEventRecord, DeviceStatus, CommandStatus
from ..schemas import (
    DeviceCreate, DeviceUpdate, DeviceResponse, DeviceDetailResponse,
    PropertyWithValueResponse, CommandResponse, DeviceEventRecordResponse,
    CommandSendRequest, CommandCreate
)
from ..mqtt.service import mqtt_service

router = APIRouter(prefix="/devices", tags=["设备管理"])

logger = logging.getLogger(__name__)


def _generate_device_key(length: int = 16) -> str:
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choices(chars, k=length))


def _generate_device_secret(length: int = 32) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def _try_enum(enum_cls, value):
    if value is None:
        return None
    try:
        return enum_cls(value)
    except (ValueError, TypeError):
        return value


@router.get("/", response_model=List[DeviceResponse])
async def list_devices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取设备列表（支持分页、产品过滤、状态过滤）"""
    query = select(Device).where(Device.owner_id == current_user.id)
    if product_id is not None:
        query = query.where(Device.product_id == product_id)
    if status:
        status_enum = _try_enum(DeviceStatus, status)
        query = query.where(Device.status == status_enum)
    query = query.order_by(desc(Device.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{device_id}", response_model=DeviceDetailResponse)
async def get_device(
    device_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取设备详情（包含属性当前值、最近命令、最近事件）"""
    result = await db.execute(
        select(Device).options(
            selectinload(Device.product).selectinload(Product.properties)
        ).where(
            Device.id == device_id,
            Device.owner_id == current_user.id,
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # 获取每个属性的最新遥测值
    props_with_value: List[PropertyWithValueResponse] = []
    for prop in device.product.properties:
        telemetry_result = await db.execute(
            select(Telemetry)
            .where(
                Telemetry.device_id == device.id,
                Telemetry.property_identifier == prop.identifier,
            )
            .order_by(desc(Telemetry.timestamp))
            .limit(1)
        )
        telemetry = telemetry_result.scalar_one_or_none()
        props_with_value.append(PropertyWithValueResponse(
            identifier=prop.identifier,
            name=prop.name,
            data_type=prop.data_type,
            unit=prop.unit,
            current_value=telemetry.value if telemetry else None,
            last_updated=telemetry.timestamp if telemetry else None,
        ))

    # 获取最近 10 条命令
    commands_result = await db.execute(
        select(Command).where(Command.device_id == device.id).order_by(desc(Command.created_at)).limit(10)
    )
    recent_commands = commands_result.scalars().all()

    # 获取最近 10 条事件
    events_result = await db.execute(
        select(DeviceEventRecord).where(DeviceEventRecord.device_id == device.id).order_by(desc(DeviceEventRecord.timestamp)).limit(10)
    )
    recent_events = events_result.scalars().all()

    return DeviceDetailResponse(
        id=device.id,
        device_key=device.device_key,
        device_name=device.device_name,
        product_id=device.product_id,
        product_name=device.product.name,
        status=device.status,
        last_seen=device.last_seen,
        owner_id=device.owner_id,
        extra=device.extra,
        created_at=device.created_at,
        properties=props_with_value,
        recent_commands=recent_commands,
        recent_events=recent_events,
    )


@router.post("/", response_model=DeviceResponse)
async def create_device(
    device_data: DeviceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建新设备（自动生成 device_key 和 device_secret）"""
    # 验证产品存在且属于当前用户
    product_result = await db.execute(
        select(Product).where(
            Product.id == device_data.product_id,
            Product.owner_id == current_user.id,
        )
    )
    product = product_result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_device = Device(
        device_key=_generate_device_key(),
        device_secret=_generate_device_secret(),
        device_name=device_data.device_name,
        product_id=device_data.product_id,
        owner_id=current_user.id,
        extra=device_data.extra,
    )
    db.add(new_device)
    await db.commit()
    await db.refresh(new_device)
    return new_device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device_data: DeviceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新设备名称或扩展信息"""
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.owner_id == current_user.id,
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    for field, value in device_data.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    await db.commit()
    await db.refresh(device)
    return device


@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除设备"""
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.owner_id == current_user.id,
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    await db.delete(device)
    await db.commit()
    return {"message": "Device deleted successfully"}


@router.post("/{device_id}/regenerate-key", response_model=DeviceResponse)
async def regenerate_device_secret(
    device_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """重新生成设备密钥"""
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.owner_id == current_user.id,
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    device.device_secret = _generate_device_secret()
    await db.commit()
    await db.refresh(device)
    return device


@router.get("/{device_id}/properties", response_model=List[PropertyWithValueResponse])
async def get_device_properties(
    device_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取设备属性列表及其当前值"""
    result = await db.execute(
        select(Device).options(
            selectinload(Device.product).selectinload(Product.properties)
        ).where(
            Device.id == device_id,
            Device.owner_id == current_user.id,
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    props_with_value = []
    for prop in device.product.properties:
        telemetry_result = await db.execute(
            select(Telemetry)
            .where(
                Telemetry.device_id == device.id,
                Telemetry.property_identifier == prop.identifier,
            )
            .order_by(desc(Telemetry.timestamp))
            .limit(1)
        )
        telemetry = telemetry_result.scalar_one_or_none()
        props_with_value.append(PropertyWithValueResponse(
            identifier=prop.identifier,
            name=prop.name,
            data_type=prop.data_type,
            unit=prop.unit,
            current_value=telemetry.value if telemetry else None,
            last_updated=telemetry.timestamp if telemetry else None,
        ))
    return props_with_value


@router.post("/{device_id}/commands", response_model=CommandResponse)
async def send_command_to_device(
    device_id: int,
    command_data: CommandSendRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """向设备发送命令（通过 MQTT 下发）"""
    result = await db.execute(
        select(Device).options(selectinload(Device.product).selectinload(Product.services)).where(
            Device.id == device_id,
            Device.owner_id == current_user.id,
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # 验证服务标识符存在于该产品的服务列表中
    valid_services = {s.identifier for s in device.product.services}
    if command_data.service_identifier not in valid_services:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service identifier. Available services: {', '.join(valid_services) if valid_services else 'none'}"
        )

    command_id = f"cmd-{uuid.uuid4()}"
    params = command_data.parameters if command_data.parameters is not None else command_data.input_params
    new_command = Command(
        command_id=command_id,
        device_id=device_id,
        service_identifier=command_data.service_identifier,
        input_params=params,
        status=CommandStatus.PENDING,
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(new_command)
    await db.flush()

    # 通过 MQTT 发布命令
    mqtt_success = False
    try:
        if mqtt_service is not None and hasattr(mqtt_service, '_connected') and mqtt_service._connected:
            topic = f"devices/{device.device_key}/commands"
            payload = {
                "command_id": command_id,
                "service_identifier": command_data.service_identifier,
                "input_params": params,
                "timestamp": datetime.utcnow().isoformat(),
            }
            mqtt_service.client.publish(topic, json.dumps(payload))
            new_command.status = CommandStatus.SENT
            new_command.sent_at = datetime.utcnow()
            mqtt_success = True
        else:
            logger.info(f"MQTT not connected, saving command as PENDING for device_id={device_id}")
    except Exception as e:
        logger.exception(f"Failed to publish MQTT command: {e}")

    await db.commit()
    await db.refresh(new_command)
    return new_command


@router.get("/{device_id}/commands", response_model=List[CommandResponse])
async def list_device_commands(
    device_id: int,
    limit: int = Query(50, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取设备命令列表"""
    # 验证设备存在且属于当前用户
    device_result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.owner_id == current_user.id,
        )
    )
    if not device_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Device not found")

    result = await db.execute(
        select(Command)
        .where(Command.device_id == device_id)
        .order_by(desc(Command.created_at))
        .limit(limit)
    )
    return result.scalars().all()
