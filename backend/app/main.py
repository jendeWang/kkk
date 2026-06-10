from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .database import init_db, async_session_maker
from .api import auth, products, devices, telemetry, commands, alerts, apikeys, sse
from .services.init_service import init_default_user
from .services.sse_service import sse_service
from .mqtt.service import mqtt_service
from .config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting IOTPlatform...")
    # Initialize database
    await init_db()
    print("Database initialized")

    # Initialize default user
    async with async_session_maker() as db:
        await init_default_user(db)

    # Start MQTT service
    await mqtt_service.start(async_session_maker)

    yield

    # Shutdown
    print("Shutting down IOTPlatform...")
    await mqtt_service.stop()


app = FastAPI(
    title="IOTPlatform API",
    description="物联网设备管理平台API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(products.router, prefix=settings.API_V1_PREFIX)
app.include_router(devices.router, prefix=settings.API_V1_PREFIX)
app.include_router(telemetry.router, prefix=settings.API_V1_PREFIX)
app.include_router(commands.router, prefix=settings.API_V1_PREFIX)
app.include_router(alerts.router, prefix=settings.API_V1_PREFIX)
app.include_router(apikeys.router, prefix=settings.API_V1_PREFIX)
app.include_router(sse.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {"message": "IOTPlatform API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
