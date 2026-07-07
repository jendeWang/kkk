from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .core.database import init_db, async_session_maker
from .core.logging import setup_logging, get_logger
from .core.config import settings
from .modules.core.api import router as core_router
from .modules.devices.api import router as devices_router
from .modules.ai.api import router as ai_router
from .modules.agents.api import router as agents_router
from .modules.knowledge.api import router as knowledge_router
from .services.init_service import init_default_user, init_greenhouse_product, init_default_group, init_default_scenes
from .services.sse_service import sse_service
from .services.simulator_service import simulator_service
from .mqtt.service import mqtt_service

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting IOTPlatform...")
    setup_logging()
    await init_db()
    logger.info("Database initialized")

    async with async_session_maker() as db:
        await init_default_user(db)
        await init_greenhouse_product(db)
        await init_default_group(db)
        await init_default_scenes(db)

    await mqtt_service.start(async_session_maker)
    await simulator_service.start(async_session_maker)

    yield

    logger.info("Shutting down IOTPlatform...")
    await mqtt_service.stop()
    await simulator_service.stop()


app = FastAPI(
    title="IOTPlatform API",
    description="物联网设备管理平台API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(core_router, prefix=settings.API_V1_PREFIX)
app.include_router(devices_router, prefix=settings.API_V1_PREFIX)
app.include_router(ai_router, prefix=settings.API_V1_PREFIX)
app.include_router(agents_router, prefix=settings.API_V1_PREFIX)
app.include_router(knowledge_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {"message": "IOTPlatform API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/services")
async def list_services():
    return {
        "services": [
            {"name": "core", "path": f"{settings.API_V1_PREFIX}/", "description": "核心服务（认证、用户、系统）"},
            {"name": "devices", "path": f"{settings.API_V1_PREFIX}/", "description": "设备服务（设备管理、遥测、命令）"},
            {"name": "ai", "path": f"{settings.API_V1_PREFIX}/ai", "description": "AI推理服务"},
            {"name": "agents", "path": f"{settings.API_V1_PREFIX}/agents", "description": "多智能体服务"},
            {"name": "knowledge", "path": f"{settings.API_V1_PREFIX}/knowledge", "description": "知识图谱服务"},
        ]
    }