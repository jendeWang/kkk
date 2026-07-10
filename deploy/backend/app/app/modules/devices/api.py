from fastapi import APIRouter
from ...api import devices, telemetry, commands, products, groups, scenes, alerts, sse, tasks

router = APIRouter()

router.include_router(devices.router)
router.include_router(telemetry.router)
router.include_router(commands.router)
router.include_router(products.router)
router.include_router(groups.router)
router.include_router(scenes.router)
router.include_router(alerts.router)
router.include_router(sse.router)
router.include_router(tasks.router)