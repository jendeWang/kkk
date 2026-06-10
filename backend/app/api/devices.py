from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
import secrets
from .deps import get_current_active_user
from ..database import get_db
from ..models.models import User, Device, Product, Telemetry, Command, DeviceStatusEnum, CommandStatusEnum
from ..schemas import (
    DeviceCreate, DeviceUpdate, DeviceResponse, DeviceDetailResponse,
    TelemetryResponse, CommandCreate, CommandResponse
)
from ..mqtt.service import mqtt_service

router = APIRouter(prefix="/devices", tags=["设备管理"])


def generate_device_credentials():
    """生成设备密钥对"""
    device_key = 'dev_' + ''.join(secrets.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=24))
    device_secret = ''.join(secrets.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=48))
    return device_key, device_secret


@router.post("/", response_model=DeviceResponse)
async def create_device(
    device: DeviceCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建设备"""
    # 验证产品存在且属于当前用户
    result = await db.execute(
        select(Product).where(
            Product.id == device.product_id,
            Product.owner_id == current_user.id
        )
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    device_key, device_secret = generate_device_credentials()
    db_device = Device(
        device_key=device_key,
        device_secret=device_secret,
        device_name=device.device_name,
        product_id=device.product_id,
        status=DeviceStatusEnum.OFFLINE,
        owner_id=current_user.id,
        extra=device.extra
    )
    db.add(db_device)
    await db.commit()
    await db.refresh(db_device)
    return db_device


@router.get("/", response_model=List[DeviceResponse])
async def list_devices(
    product_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取设备列表"""
    query = select(Device).where(Device.owner_id == current_user.id)
    if product_id:
        query = query.where(Device.product_id == product_id)
    if status:
        query = query.where(Device.status == status)

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{device_id}", response_model=DeviceDetailResponse)
async def get_device(
    device_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取设备详情"""
    result = await db.execute(
        select(Device)
        .options(selectinload(Device.product))
        .where(
            Device.id == device_id,
            Device.owner_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.put("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: int,
    device: DeviceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """更新设备"""
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.owner_id == current_user.id
        )
    )
    db_device = result.scalar_one_or_none()
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")

    for key, value in device.model_dump(exclude_unset=True).items():
        setattr(db_device, key, value)

    await db.commit()
    await db.refresh(db_device)
    return db_device


@router.delete("/{device_id}")
async def delete_device(
    device_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除设备"""
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.owner_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    await db.delete(device)
    await db.commit()
    return {"message": "Device deleted successfully"}


@router.post("/{device_id}/regenerate-secret", response_model=DeviceResponse)
async def regenerate_device_secret(
    device_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """重新生成设备密钥"""
    result = await db.execute(
        select(Device).where(
            Device.id == device_id,
            Device.owner_id == current_user.id
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    _, new_secret = generate_device_credentials()
    device.device_secret = new_secret
    await db.commit()
    await db.refresh(device)
    return device
