from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.models import User
from ..security.auth import get_password_hash
from ..config import settings


async def init_default_user(db: AsyncSession):
    """创建默认管理员用户"""
    result = await db.execute(select(User).where(User.username == "admin"))
    existing = result.scalar_one_or_none()
    if not existing:
        admin = User(
            username="admin",
            email="admin@iot.local",
            full_name="IoT Platform Administrator",
            hashed_password=get_password_hash("admin123"),
            is_active=True,
            is_superuser=True,
        )
        db.add(admin)
        await db.commit()
        print("[Init] Default admin user created: admin / admin123")
    else:
        print("[Init] Admin user already exists")
