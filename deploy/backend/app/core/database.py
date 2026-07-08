from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text, inspect
from .config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def _migrate_alert_rules(conn):
    columns = await conn.run_sync(lambda sync_conn: [
        col['name'] for col in inspect(sync_conn).get_columns('alert_rules')
    ])
    
    if 'linked_scene_id' not in columns:
        await conn.execute(text("ALTER TABLE alert_rules ADD COLUMN linked_scene_id INTEGER"))
    
    if 'auto_execute_scene' not in columns:
        await conn.execute(text("ALTER TABLE alert_rules ADD COLUMN auto_execute_scene INTEGER DEFAULT 0"))


async def _migrate_users(conn):
    columns = await conn.run_sync(lambda sync_conn: [
        col['name'] for col in inspect(sync_conn).get_columns('users')
    ])
    
    if 'role' not in columns:
        await conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'viewer'"))


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _migrate_alert_rules(conn)
        await _migrate_users(conn)