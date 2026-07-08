from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional

from .deps import get_current_active_user, get_db
from ..models.models import User, DeviceGroup, DeviceGroupMember, Device
from ..schemas import (
    DeviceGroupCreate, DeviceGroupUpdate, DeviceGroupResponse,
    DeviceGroupMemberAdd, DeviceGroupMemberRemove, DeviceResponse,
)

router = APIRouter(prefix="/groups", tags=["设备分组"])


@router.get("/", response_model=List[DeviceGroupResponse])
async def list_groups(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取分组列表（支持分页）"""
    query = select(DeviceGroup).where(DeviceGroup.owner_id == current_user.id)
    query = query.order_by(desc(DeviceGroup.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    groups = result.scalars().all()

    group_ids = [g.id for g in groups]
    count_result = await db.execute(
        select(DeviceGroupMember.group_id, func.count(DeviceGroupMember.id))
        .where(DeviceGroupMember.group_id.in_(group_ids))
        .group_by(DeviceGroupMember.group_id)
    )
    device_counts = {row[0]: row[1] for row in count_result.all()}

    response = []
    for g in groups:
        response.append(DeviceGroupResponse(
            id=g.id,
            name=g.name,
            description=g.description,
            owner_id=g.owner_id,
            created_at=g.created_at,
            updated_at=g.updated_at,
            device_count=device_counts.get(g.id, 0),
        ))
    return response


@router.post("/", response_model=DeviceGroupResponse)
async def create_group(
    group_data: DeviceGroupCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建设备分组"""
    new_group = DeviceGroup(
        name=group_data.name,
        description=group_data.description,
        owner_id=current_user.id,
    )
    db.add(new_group)
    await db.commit()
    await db.refresh(new_group)
    return DeviceGroupResponse(
        id=new_group.id,
        name=new_group.name,
        description=new_group.description,
        owner_id=new_group.owner_id,
        created_at=new_group.created_at,
        updated_at=new_group.updated_at,
        device_count=0,
    )


@router.get("/{group_id}", response_model=DeviceGroupResponse)
async def get_group(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取分组详情"""
    result = await db.execute(
        select(DeviceGroup).where(
            DeviceGroup.id == group_id,
            DeviceGroup.owner_id == current_user.id,
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    count_result = await db.execute(
        select(func.count(DeviceGroupMember.id))
        .where(DeviceGroupMember.group_id == group_id)
    )
    device_count = count_result.scalar() or 0

    return DeviceGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        owner_id=group.owner_id,
        created_at=group.created_at,
        updated_at=group.updated_at,
        device_count=device_count,
    )


@router.put("/{group_id}", response_model=DeviceGroupResponse)
async def update_group(
    group_id: int,
    group_data: DeviceGroupUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新分组信息"""
    result = await db.execute(
        select(DeviceGroup).where(
            DeviceGroup.id == group_id,
            DeviceGroup.owner_id == current_user.id,
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    for field, value in group_data.model_dump(exclude_unset=True).items():
        setattr(group, field, value)
    await db.commit()
    await db.refresh(group)

    count_result = await db.execute(
        select(func.count(DeviceGroupMember.id))
        .where(DeviceGroupMember.group_id == group_id)
    )
    device_count = count_result.scalar() or 0

    return DeviceGroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        owner_id=group.owner_id,
        created_at=group.created_at,
        updated_at=group.updated_at,
        device_count=device_count,
    )


@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除分组"""
    result = await db.execute(
        select(DeviceGroup).where(
            DeviceGroup.id == group_id,
            DeviceGroup.owner_id == current_user.id,
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    await db.delete(group)
    await db.commit()
    return {"message": "Group deleted successfully"}


@router.get("/{group_id}/devices", response_model=List[DeviceResponse])
async def list_group_devices(
    group_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取分组下的设备列表"""
    group_result = await db.execute(
        select(DeviceGroup).where(
            DeviceGroup.id == group_id,
            DeviceGroup.owner_id == current_user.id,
        )
    )
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    query = (
        select(Device)
        .join(DeviceGroupMember, DeviceGroupMember.device_id == Device.id)
        .where(DeviceGroupMember.group_id == group_id)
        .order_by(desc(DeviceGroupMember.joined_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{group_id}/devices")
async def add_devices_to_group(
    group_id: int,
    member_data: DeviceGroupMemberAdd,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """批量添加设备到分组"""
    group_result = await db.execute(
        select(DeviceGroup).where(
            DeviceGroup.id == group_id,
            DeviceGroup.owner_id == current_user.id,
        )
    )
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if not member_data.device_ids:
        return {"message": "No device IDs provided", "added": 0}

    devices_result = await db.execute(
        select(Device.id).where(
            Device.id.in_(member_data.device_ids),
            Device.owner_id == current_user.id,
        )
    )
    valid_device_ids = {row[0] for row in devices_result.all()}
    invalid_ids = set(member_data.device_ids) - valid_device_ids
    if invalid_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid device IDs: {sorted(invalid_ids)}",
        )

    existing_result = await db.execute(
        select(DeviceGroupMember.device_id).where(
            DeviceGroupMember.group_id == group_id,
            DeviceGroupMember.device_id.in_(member_data.device_ids),
        )
    )
    existing_device_ids = {row[0] for row in existing_result.all()}

    new_device_ids = [did for did in member_data.device_ids if did not in existing_device_ids]
    for device_id in new_device_ids:
        member = DeviceGroupMember(group_id=group_id, device_id=device_id)
        db.add(member)

    await db.commit()
    return {"message": "Devices added to group successfully", "added": len(new_device_ids)}


@router.delete("/{group_id}/devices")
async def remove_devices_from_group(
    group_id: int,
    member_data: DeviceGroupMemberRemove,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """批量从分组移除设备"""
    group_result = await db.execute(
        select(DeviceGroup).where(
            DeviceGroup.id == group_id,
            DeviceGroup.owner_id == current_user.id,
        )
    )
    group = group_result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if not member_data.device_ids:
        return {"message": "No device IDs provided", "removed": 0}

    result = await db.execute(
        select(DeviceGroupMember).where(
            DeviceGroupMember.group_id == group_id,
            DeviceGroupMember.device_id.in_(member_data.device_ids),
        )
    )
    members = result.scalars().all()
    removed_count = len(members)
    for member in members:
        await db.delete(member)

    await db.commit()
    return {"message": "Devices removed from group successfully", "removed": removed_count}
