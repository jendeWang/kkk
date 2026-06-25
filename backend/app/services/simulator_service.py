import asyncio
import random
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from ..models.models import Device, DeviceShadow, Product, Telemetry
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
        now = datetime.utcnow()

        sensor_configs = [
            ("temperature", 25.0, 15.0, 35.0, 0.5),
            ("humidity", 55.0, 30.0, 90.0, 1.0),
            ("light_intensity", 5000.0, 500.0, 80000.0, 500),
            ("soil_moisture", 45.0, 20.0, 90.0, 0.8),
            ("co2", 800.0, 300.0, 2000.0, 50),
            ("soil_temperature", 22.0, 10.0, 35.0, 0.3),
        ]

        for prop_id, default_val, min_val, max_val, max_change in sensor_configs:
            if prop_id in reported:
                base = reported.get(prop_id, default_val)
                change = random.uniform(-max_change, max_change)
                new_val = round(max(min_val, min(max_val, base + change)), 1 if max_change < 1 else 0)
                reported[prop_id] = new_val
                
                telemetry = Telemetry(
                    device_id=device_id,
                    property_identifier=prop_id,
                    value=str(new_val),
                    timestamp=now,
                    quality="good"
                )
                db.add(telemetry)

        shadow.reported = reported
        shadow.version += 1
        shadow.last_updated = now


simulator_service = DeviceSimulator()
