from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from ..security.auth import decode_token
from ..core.database import get_db
from ..models.models import User, APIKey
from ..core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


async def get_token_from_request(
    request: Request,
    token: str = Depends(oauth2_scheme)
) -> str:
    """从请求中获取token，支持Header和URL参数"""
    query_token = request.query_params.get('token')
    if query_token:
        return query_token
    return token


async def _get_user_by_jwt(token: str, db: AsyncSession) -> User | None:
    """通过 JWT token 获取用户"""
    payload = decode_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    result = await db.execute(select(User).where(User.id == int(user_id)))
    return result.scalar_one_or_none()


async def _get_user_by_api_key(token: str, db: AsyncSession) -> User | None:
    """通过 API Key 获取用户"""
    result = await db.execute(
        select(APIKey).where(
            APIKey.key == token,
            APIKey.is_active == True,
        )
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        return None
    # 检查过期
    if api_key.expires_at and api_key.expires_at < datetime.utcnow():
        return None
    # 更新最后使用时间
    await db.execute(
        update(APIKey).where(APIKey.id == api_key.id).values(last_used=datetime.utcnow())
    )
    await db.commit()
    # 获取关联用户
    result = await db.execute(select(User).where(User.id == api_key.user_id))
    return result.scalar_one_or_none()


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    获取当前用户 — 同时支持 JWT Bearer Token 和 API Key Bearer Token
    - JWT: Authorization: Bearer eyJhbG...
    - API Key: Authorization: Bearer <32位随机字符串>
    - SSE场景: ?token=<api_key> 或 ?api_key=<api_key>
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. 优先从 URL query 参数获取（SSE 长连接场景）
    token = request.query_params.get('token') or request.query_params.get('api_key')
    user = None
    if token:
        # 判断是 JWT 还是 API Key（JWT 以 eyJ 开头）
        if token.startswith('eyJ'):
            user = await _get_user_by_jwt(token, db)
        else:
            user = await _get_user_by_api_key(token, db)
        if user and user.is_active:
            return user

    # 2. 从 Authorization Header 获取
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        if token:
            if token.startswith('eyJ'):
                user = await _get_user_by_jwt(token, db)
            else:
                user = await _get_user_by_api_key(token, db)
            if user and user.is_active:
                return user

    raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user
