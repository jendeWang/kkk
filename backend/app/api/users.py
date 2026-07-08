from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from .deps import get_current_active_user, get_current_superuser
from ..core.database import get_db
from ..models.models import User
from ..schemas import UserResponse, UserCreate, UserUpdate
from ..security.auth import get_password_hash, verify_password

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("/roles")
async def list_roles(
    current_user: User = Depends(get_current_active_user),
):
    """获取角色列表及权限说明"""
    from .deps import ROLE_PERMISSIONS
    roles_info = [
        {
            "key": "admin",
            "name": "管理员",
            "description": "拥有全部权限，可管理用户、设备、数据、规则等",
            "permissions": ROLE_PERMISSIONS.get("admin", []),
        },
        {
            "key": "operator",
            "name": "操作员",
            "description": "可操作设备、查看数据、配置告警和规则，不可管理用户",
            "permissions": ROLE_PERMISSIONS.get("operator", []),
        },
        {
            "key": "viewer",
            "name": "查看员",
            "description": "只能查看设备和数据，不可操作",
            "permissions": ROLE_PERMISSIONS.get("viewer", []),
        },
    ]
    return roles_info


@router.get("/", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(desc(User.created_at)))
    return result.scalars().all()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    if len(user_data.username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be at least 3 characters"
        )
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )

    result = await db.execute(select(User).where(User.username == user_data.username))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
        role=user_data.role or "viewer",
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user_data.email is not None:
        user.email = user_data.email
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.is_superuser is not None:
        user.is_superuser = user_data.is_superuser
    if user_data.role is not None:
        user.role = user_data.role

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
):
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    return {"message": "User deleted successfully"}


@router.put("/me/password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if len(new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )

    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )

    current_user.hashed_password = get_password_hash(new_password)
    await db.commit()
    return {"message": "Password changed successfully"}


@router.put("/me/profile", response_model=UserResponse)
async def update_profile(
    email: str = None,
    full_name: str = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if email is not None:
        current_user.email = email
    if full_name is not None:
        current_user.full_name = full_name

    await db.commit()
    await db.refresh(current_user)
    return current_user