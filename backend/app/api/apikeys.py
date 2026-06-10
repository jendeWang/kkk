from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from datetime import datetime, timedelta
import secrets
import random
import string

from .deps import get_current_active_user, get_db
from ..models.models import User, APIKey
from ..schemas import APIKeyCreate, APIKeyResponse

router = APIRouter(prefix="/api-keys", tags=["API密钥管理"])


def _generate_key(length: int = 32) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


@router.post("/", response_model=APIKeyResponse)
async def create_api_key(
    api_key: APIKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """创建 API 密钥"""
    key = _generate_key()
    expires_at = api_key.expires_at or (datetime.utcnow() + timedelta(days=90))
    permissions = api_key.permissions or {"read": True, "write": True}

    db_api_key = APIKey(
        key=key,
        name=api_key.name,
        user_id=current_user.id,
        permissions=permissions,
        expires_at=expires_at,
        is_active=True,
    )
    db.add(db_api_key)
    await db.commit()
    await db.refresh(db_api_key)
    return db_api_key


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取 API 密钥列表"""
    result = await db.execute(
        select(APIKey).where(
            APIKey.user_id == current_user.id,
        ).order_by(desc(APIKey.created_at))
    )
    return result.scalars().all()


@router.delete("/{api_key_id}")
async def delete_api_key(
    api_key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除 API 密钥"""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == api_key_id,
            APIKey.user_id == current_user.id,
        )
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    await db.delete(api_key)
    await db.commit()
    return {"message": "API key deleted successfully"}
