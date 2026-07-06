from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime

from .deps import get_current_active_user
from ..core.database import get_db
from ..models.models import User, AutomationScene, AutomationExecutionLog, TriggerType, ActionType
from ..schemas import (
    AutomationSceneCreate, AutomationSceneUpdate, AutomationSceneResponse,
    AutomationExecutionLogResponse, SceneTriggerRequest
)
from ..services.scene_engine import scene_engine

router = APIRouter(prefix="/scenes", tags=["场景联动"])


def _try_enum(enum_cls, value):
    if value is None:
        return None
    try:
        return enum_cls(value)
    except (ValueError, TypeError):
        return value


@router.get("/", response_model=List[AutomationSceneResponse])
async def list_scenes(
    enabled: Optional[bool] = Query(None),
    trigger_type: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取自动化场景列表"""
    query = select(AutomationScene).where(AutomationScene.owner_id == current_user.id)
    if enabled is not None:
        query = query.where(AutomationScene.enabled == enabled)
    if trigger_type:
        trigger_enum = _try_enum(TriggerType, trigger_type)
        if trigger_enum:
            query = query.where(AutomationScene.trigger_type == trigger_enum)
    query = query.order_by(desc(AutomationScene.created_at))
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=AutomationSceneResponse)
async def create_scene(
    scene: AutomationSceneCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建自动化场景"""
    trigger_enum = _try_enum(TriggerType, scene.trigger_type)
    if not trigger_enum:
        raise HTTPException(status_code=400, detail="Invalid trigger_type")
    
    action_enum = _try_enum(ActionType, scene.action_type)
    if not action_enum:
        raise HTTPException(status_code=400, detail="Invalid action_type")

    db_scene = AutomationScene(
        name=scene.name,
        description=scene.description,
        owner_id=current_user.id,
        trigger_type=trigger_enum,
        trigger_config=scene.trigger_config,
        action_type=action_enum,
        action_config=scene.action_config,
        enabled=scene.enabled if scene.enabled is not None else True,
        cooldown_seconds=scene.cooldown_seconds or 60,
    )
    db.add(db_scene)
    await db.commit()
    await db.refresh(db_scene)
    return db_scene


@router.get("/{scene_id}", response_model=AutomationSceneResponse)
async def get_scene(
    scene_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取场景详情"""
    result = await db.execute(
        select(AutomationScene).where(
            AutomationScene.id == scene_id,
            AutomationScene.owner_id == current_user.id,
        )
    )
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene


@router.put("/{scene_id}", response_model=AutomationSceneResponse)
async def update_scene(
    scene_id: int,
    scene_update: AutomationSceneUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新场景"""
    result = await db.execute(
        select(AutomationScene).where(
            AutomationScene.id == scene_id,
            AutomationScene.owner_id == current_user.id,
        )
    )
    db_scene = result.scalar_one_or_none()
    if not db_scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    update_data = scene_update.model_dump(exclude_unset=True)
    
    if "trigger_type" in update_data:
        trigger_enum = _try_enum(TriggerType, update_data["trigger_type"])
        if not trigger_enum:
            raise HTTPException(status_code=400, detail="Invalid trigger_type")
        update_data["trigger_type"] = trigger_enum
    
    if "action_type" in update_data:
        action_enum = _try_enum(ActionType, update_data["action_type"])
        if not action_enum:
            raise HTTPException(status_code=400, detail="Invalid action_type")
        update_data["action_type"] = action_enum

    for field, value in update_data.items():
        setattr(db_scene, field, value)

    await db.commit()
    await db.refresh(db_scene)
    return db_scene


@router.delete("/{scene_id}")
async def delete_scene(
    scene_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除场景"""
    result = await db.execute(
        select(AutomationScene).where(
            AutomationScene.id == scene_id,
            AutomationScene.owner_id == current_user.id,
        )
    )
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    await db.delete(scene)
    await db.commit()
    return {"message": "Scene deleted successfully"}


@router.post("/{scene_id}/trigger", response_model=AutomationExecutionLogResponse)
async def trigger_scene_manually(
    scene_id: int,
    request: SceneTriggerRequest = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """手动触发场景"""
    result = await db.execute(
        select(AutomationScene).where(
            AutomationScene.id == scene_id,
            AutomationScene.owner_id == current_user.id,
        )
    )
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    trigger_data = request.trigger_data if request and request.trigger_data else {
        "trigger_type": "manual",
        "triggered_by": current_user.username,
    }

    log = await scene_engine.execute_scene(db, scene, trigger_data)
    return log


@router.get("/{scene_id}/executions", response_model=List[AutomationExecutionLogResponse])
async def list_scene_executions(
    scene_id: int,
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取场景执行日志"""
    scene_result = await db.execute(
        select(AutomationScene).where(
            AutomationScene.id == scene_id,
            AutomationScene.owner_id == current_user.id,
        )
    )
    scene = scene_result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    query = select(AutomationExecutionLog).where(AutomationExecutionLog.scene_id == scene_id)
    if status:
        from ..models.models import ExecutionStatus
        status_enum = _try_enum(ExecutionStatus, status)
        if status_enum:
            query = query.where(AutomationExecutionLog.status == status_enum)
    query = query.order_by(desc(AutomationExecutionLog.created_at)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{scene_id}/toggle", response_model=AutomationSceneResponse)
async def toggle_scene(
    scene_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """启用/禁用场景"""
    result = await db.execute(
        select(AutomationScene).where(
            AutomationScene.id == scene_id,
            AutomationScene.owner_id == current_user.id,
        )
    )
    scene = result.scalar_one_or_none()
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    scene.enabled = not scene.enabled
    await db.commit()
    await db.refresh(scene)
    return scene
