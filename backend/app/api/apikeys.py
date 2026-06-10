from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
import secrets
import random
from .deps import get_current_active_user
from ..database import get_db
from ..models.models import User, APIKey, PermissionLevelEnum
from ..schemas import APIKeyCreate, APIKeyResponse

router = APIRouter(prefix="/api-keys", tags=["API密钥管理"])


def generate_api_key():
    """生成API密钥"""
    chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    return ''.join(random.choices(chars, k=32))


@router.post("/", response_model=APIKeyResponse)
async def create_api_key(
    api_key: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """创建API密钥"""
    key = generate_api_key()
    db_api_key = APIKey(
        key=key,
        name=api_key.name,
        permission_level=PermissionLevelEnum(api_key.permission_level),
        owner_id=current_user.id
    )
    db.add(db_api_key)
    await db.commit()
    await db.refresh(db_api_key)
    return db_api_key


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """获取API密钥列表"""
    result = await db.execute(
        select(APIKey).where(APIKey.owner_id == current_user.id)
    )
    return result.scalars().all()


@router.delete("/{api_key_id}")
async def delete_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """删除API密钥"""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == api_key_id,
            APIKey.owner_id == current_user.id
        )
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    await db.delete(api_key)
    await db.commit()
    return {"message": "API key deleted successfully"}
