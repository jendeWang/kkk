import asyncio
import random
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from ..models.models import Device, DeviceShadow, Product
import logging

logger = logging.getLogger(__name__)


class DeviceSimulator:
    def __init__(self):
        self._running = False
        self._task = None
        self._session_maker = None
        self._interval = 3

    async def start(self, session_maker: async_sessionmaker):
        if self._running:
            return
        self._session_maker = session_maker
        self._running = True
        self._task = asyncio.create_task(self._simulate_loop())
        logger.info("Device simulator started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Device simulator stopped")

    async def _simulate_loop(self):
        while self._running:
            try:
                await self._update_all_devices()
            except Exception as e:
                logger.exception(f"Simulator error: {e}")
            await asyncio.sleep(self._interval)

    async def _update_all_devices(self):
        async with self._session_maker() as db:
            result = await db.execute(
                select(Device).where(Device.status == "online")
            )
            devices = result.scalars().all()

            for device in devices:
                await self._update_device_shadow(db, device.id)

            await db.commit()

    async def _update_device_shadow(self, db, device_id: int):
        shadow_result = await db.execute(
            select(DeviceShadow).where(DeviceShadow.device_id == device_id)
        )
        shadow = shadow_result.scalar_one_or_none()

        if not shadow:
            return

        reported = dict(shadow.reported or {})

        if "temperature" in reported:
            base = reported.get("temperature", 25.0)
            change = random.uniform(-0.5, 0.5)
            reported["temperature"] = round(max(15.0, min(35.0, base + change)), 1)

        if "humidity" in reported:
            base = reported.get("humidity", 55.0)
            change = random.uniform(-1.0, 1.0)
            reported["humidity"] = round(max(30.0, min(90.0, base + change)), 1)

        if "light_intensity" in reported:
            base = reported.get("light_intensity", 5000.0)
            change = random.uniform(-500, 500)
            reported["light_intensity"] = round(max(500.0, min(80000.0, base + change)), 0)

        if "soil_moisture" in reported:
            base = reported.get("soil_moisture", 45.0)
            change = random.uniform(-0.8, 0.8)
            reported["soil_moisture"] = round(max(20.0, min(90.0, base + change)), 1)

        if "co2" in reported:
            base = reported.get("co2", 800.0)
            change = random.uniform(-50, 50)
            reported["co2"] = round(max(300.0, min(2000.0, base + change)), 0)

        if "soil_temperature" in reported:
            base = reported.get("soil_temperature", 22.0)
            change = random.uniform(-0.3, 0.3)
            reported["soil_temperature"] = round(max(10.0, min(35.0, base + change)), 1)

        shadow.reported = reported
        shadow.version += 1
        shadow.last_updated = datetime.utcnow()


simulator_service = DeviceSimulator()
