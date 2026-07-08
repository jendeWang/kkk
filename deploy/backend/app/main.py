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
from .core.license import verify_system

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting IOTPlatform...")
    setup_logging()

    # 授权校验（必须在数据库初始化之前，防止无授权运行）
    auth_result = verify_system()
    logger.info(f"License status: {auth_result.readable_status()}")
    if not auth_result.is_valid:
        logger.error(f"System authorization failed: {auth_result.readable_status()}")
        raise RuntimeError(f"授权校验失败: {auth_result.readable_status()}")
    if auth_result.status == "readonly":
        logger.warning("License expired — system running in READ-ONLY mode")

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


# ---------------------------------------------------------------------------
# License 写操作拦截中间件
# ---------------------------------------------------------------------------
@app.middleware("http")
async def license_write_guard(request, call_next):
    """
    全局中间件：授权过期后拦截所有写操作（POST/PUT/DELETE/PATCH），
    但保留读操作（GET/HEAD/OPTIONS）可用，确保学校能看到数据并续费。
    """
    from .core.license import verify_system
    method = request.method.upper()
    if method in ("POST", "PUT", "DELETE", "PATCH"):
        result = verify_system()
        if result.status == "readonly":
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "授权已过期，当前仅支持只读访问，请联系管理员续期",
                    "status": "readonly",
                    "school": result.school,
                },
            )
    return await call_next(request)

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