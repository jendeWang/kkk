from fastapi import APIRouter
from ...api import auth, users, apikeys, operation_logs, dashboard, topology

router = APIRouter()

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(apikeys.router)
router.include_router(operation_logs.router)
router.include_router(dashboard.router)
router.include_router(topology.router)