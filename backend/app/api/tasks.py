from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime
import uuid
import json

from .deps import get_current_active_user, get_db
from ..models.models import User, Device, TimedTask, Command, CommandStatus, Product
from ..schemas import TimedTaskCreate, TimedTaskUpdate, TimedTaskResponse
from ..mqtt.service import mqtt_service

router = APIRouter(prefix="/tasks", tags=["定时任务"])


@router.get("/", response_model=List[TimedTaskResponse])
async def list_tasks(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的所有定时任务（关联device_name）"""
    result = await db.execute(
        select(TimedTask, Device.device_name)
        .join(Device, TimedTask.device_id == Device.id)
        .where(TimedTask.owner_id == current_user.id)
        .order_by(desc(TimedTask.created_at))
    )
    rows = result.all()
    
    tasks = []
    for task, device_name in rows:
        task_dict = task.__dict__.copy()
        task_dict.pop('_sa_instance_state', None)
        task_dict['device_name'] = device_name
        tasks.append(task_dict)
    
    return tasks


@router.post("/", response_model=TimedTaskResponse)
async def create_task(
    task_data: TimedTaskCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建定时任务"""
    device_result = await db.execute(
        select(Device).where(
            Device.id == task_data.device_id,
            Device.owner_id == current_user.id,
        )
    )
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    new_task = TimedTask(
        name=task_data.name,
        device_id=task_data.device_id,
        property_identifier=task_data.property_identifier,
        target_value=task_data.target_value,
        cron_expression=task_data.cron_expression,
        enabled=task_data.enabled,
        description=task_data.description,
        owner_id=current_user.id,
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    result = TimedTaskResponse.model_validate(new_task)
    result.device_name = device.device_name
    return result


@router.put("/{task_id}", response_model=TimedTaskResponse)
async def update_task(
    task_id: int,
    task_data: TimedTaskUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新定时任务"""
    result = await db.execute(
        select(TimedTask).join(Device).where(
            TimedTask.id == task_id,
            TimedTask.owner_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task_data.device_id is not None:
        device_result = await db.execute(
            select(Device).where(
                Device.id == task_data.device_id,
                Device.owner_id == current_user.id,
            )
        )
        device = device_result.scalar_one_or_none()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
    
    for field, value in task_data.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    
    await db.commit()
    await db.refresh(task)
    
    device_result = await db.execute(
        select(Device).where(Device.id == task.device_id)
    )
    device = device_result.scalar_one_or_none()
    
    result = TimedTaskResponse.model_validate(task)
    result.device_name = device.device_name if device else None
    return result


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除定时任务"""
    result = await db.execute(
        select(TimedTask).join(Device).where(
            TimedTask.id == task_id,
            TimedTask.owner_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete(task)
    await db.commit()
    return {"message": "Task deleted successfully"}


@router.post("/{task_id}/toggle", response_model=TimedTaskResponse)
async def toggle_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """启用/禁用任务"""
    result = await db.execute(
        select(TimedTask).join(Device).where(
            TimedTask.id == task_id,
            TimedTask.owner_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.enabled = not task.enabled
    await db.commit()
    await db.refresh(task)
    
    device_result = await db.execute(
        select(Device).where(Device.id == task.device_id)
    )
    device = device_result.scalar_one_or_none()
    
    result = TimedTaskResponse.model_validate(task)
    result.device_name = device.device_name if device else None
    return result


@router.post("/{task_id}/run")
async def run_task(
    task_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """立即执行任务（调用device command API）"""
    result = await db.execute(
        select(TimedTask).join(Device).where(
            TimedTask.id == task_id,
            TimedTask.owner_id == current_user.id,
        )
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if not task.enabled:
        raise HTTPException(status_code=400, detail="Task is disabled")
    
    device_result = await db.execute(
        select(Device).options(
            selectinload(Device.product).selectinload(Product.services)
        ).where(Device.id == task.device_id)
    )
    device = device_result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    valid_services = {s.identifier for s in device.product.services}
    if task.property_identifier not in valid_services:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service identifier. Available services: {', '.join(valid_services) if valid_services else 'none'}"
        )
    
    command_id = f"cmd-{uuid.uuid4()}"
    new_command = Command(
        command_id=command_id,
        device_id=task.device_id,
        service_identifier=task.property_identifier,
        input_params=task.target_value,
        status=CommandStatus.PENDING,
        owner_id=current_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(new_command)
    await db.flush()
    
    try:
        if mqtt_service is not None and hasattr(mqtt_service, '_connected') and mqtt_service._connected:
            topic = f"devices/{device.device_key}/commands"
            payload = {
                "command_id": command_id,
                "service_identifier": task.property_identifier,
                "input_params": task.target_value,
                "timestamp": datetime.utcnow().isoformat(),
            }
            mqtt_service.client.publish(topic, json.dumps(payload))
            new_command.status = CommandStatus.SENT
            new_command.sent_at = datetime.utcnow()
    except Exception as e:
        print(f"MQTT publish error: {e}")
    
    task.last_run_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(new_command)
    await db.refresh(task)
    
    return {
        "message": "Task executed successfully",
        "task_id": task.id,
        "command_id": new_command.command_id,
        "command_status": new_command.status.value,
    }