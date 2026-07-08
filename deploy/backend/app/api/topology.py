from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from .deps import get_current_active_user, get_db
from ..models.models import User, TopologyConfig
from ..schemas import TopologyConfigResponse, TopologyConfigUpdate

router = APIRouter(prefix="/topology", tags=["拓扑配置"])


@router.get("/config", response_model=TopologyConfigResponse)
async def get_topology_config(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的拓扑配置"""
    result = await db.execute(
        select(TopologyConfig).where(TopologyConfig.owner_id == current_user.id)
    )
    config = result.scalar_one_or_none()

    if not config:
        config = TopologyConfig(
            owner_id=current_user.id,
            canvas_width=1200,
            canvas_height=800,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)

    return config


@router.put("/config", response_model=TopologyConfigResponse)
async def update_topology_config(
    config_data: TopologyConfigUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """更新拓扑配置"""
    result = await db.execute(
        select(TopologyConfig).where(TopologyConfig.owner_id == current_user.id)
    )
    config = result.scalar_one_or_none()

    if not config:
        config = TopologyConfig(
            owner_id=current_user.id,
            canvas_width=1200,
            canvas_height=800,
        )
        db.add(config)
        await db.flush()

    update_data = config_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)
    return config
