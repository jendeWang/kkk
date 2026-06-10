from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.models import User
from ..security.auth import get_password_hash


async def init_default_user(db: AsyncSession):
    """初始化默认管理员账号"""
    result = await db.execute(select(User).where(User.username == "admin"))
    existing_user = result.scalar_one_or_none()

    if not existing_user:
        admin_user = User(
            username="admin",
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            is_active=True
        )
        db.add(admin_user)
        await db.commit()
        print("Default admin user created: admin / admin123")
    else:
        print("Admin user already exists")
