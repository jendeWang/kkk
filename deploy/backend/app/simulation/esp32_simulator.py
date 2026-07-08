import asyncio
import random
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from ..core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SensorConfig:
    identifier: str
    name: str
    unit: str
    min_value: float
    max_value: float
    default_value: float
    variance: float
    decimal_places: int = 1


@dataclass
class ActuatorConfig:
    identifier: str
    name: str
    default_state: bool = False


@dataclass
class ESP32Node:
    node_id: str = field(default_factory=lambda: f"esp32_{uuid.uuid4().hex[:8]}")
    node_name: str = "ESP32 Node"
    product_key: str = "smart_greenhouse"
    status: str = "online"
    sensors: Dict[str, float] = field(default_factory=dict)
    actuators: Dict[str, bool] = field(default_factory=dict)
    last_heartbeat: Optional[datetime] = None
    sampling_interval: float = 3.0
    _task: Optional[asyncio.Task] = None
    _running: bool = False
    _on_data_callback: Optional[Callable] = None

    def update_sensor_value(self, identifier: str, value: float):
        if identifier in self.sensors:
            self.sensors[identifier] = value
            if self._on_data_callback:
                self._on_data_callback({
                    "node_id": self.node_id,
                    "node_name": self.node_name,
                    "property_identifier": identifier,
                    "value": value,
                    "timestamp": datetime.utcnow().isoformat()
                })

    def set_actuator_state(self, identifier: str, state: bool):
        self.actuators[identifier] = state
        logger.info(f"[{self.node_name}] Actuator {identifier} set to {state}")


DEFAULT_SENSORS = [
    SensorConfig("temperature", "空气温度", "°C", 10.0, 40.0, 25.0, 0.5),
    SensorConfig("humidity", "空气湿度", "%RH", 20.0, 95.0, 55.0, 1.0),
    SensorConfig("light_intensity", "光照强度", "lux", 0.0, 100000.0, 5000.0, 500.0),
    SensorConfig("soil_moisture", "土壤湿度", "%", 10.0, 95.0, 45.0, 0.8),
    SensorConfig("co2", "CO₂浓度", "ppm", 300.0, 3000.0, 800.0, 50.0),
    SensorConfig("soil_temperature", "土壤温度", "°C", 5.0, 35.0, 22.0, 0.3),
]

DEFAULT_ACTUATORS = [
    ActuatorConfig("fan_status", "通风扇"),
    ActuatorConfig("light_status", "补光灯"),
    ActuatorConfig("pump_status", "灌溉水泵"),
]


class ESP32SimulatorManager:
    def __init__(self):
        self._nodes: Dict[str, ESP32Node] = {}
        self._sensor_configs: List[SensorConfig] = DEFAULT_SENSORS
        self._actuator_configs: List[ActuatorConfig] = DEFAULT_ACTUATORS
        self._global_callback: Optional[Callable] = None

    def set_global_callback(self, callback: Callable):
        self._global_callback = callback

    def create_node(self, node_name: str = None, product_key: str = None) -> ESP32Node:
        node = ESP32Node(
            node_name=node_name or f"ESP32 Node {len(self._nodes) + 1}",
            product_key=product_key or "smart_greenhouse"
        )
        
        for sensor in self._sensor_configs:
            node.sensors[sensor.identifier] = sensor.default_value
        
        for actuator in self._actuator_configs:
            node.actuators[actuator.identifier] = actuator.default_state
        
        node._on_data_callback = self._global_callback
        self._nodes[node.node_id] = node
        logger.info(f"Created ESP32 node: {node.node_id} ({node.node_name})")
        return node

    def get_node(self, node_id: str) -> Optional[ESP32Node]:
        return self._nodes.get(node_id)

    def list_nodes(self) -> List[ESP32Node]:
        return list(self._nodes.values())

    async def remove_node(self, node_id: str):
        node = self._nodes.pop(node_id, None)
        if node:
            await self.stop_node(node_id)
            logger.info(f"Removed ESP32 node: {node_id}")

    async def start_node(self, node_id: str):
        node = self._nodes.get(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")
        
        if node._running:
            return
        
        node._running = True
        node._task = asyncio.create_task(self._sensor_loop(node))
        logger.info(f"Started ESP32 node: {node_id}")

    async def stop_node(self, node_id: str):
        node = self._nodes.get(node_id)
        if not node:
            return
        
        node._running = False
        if node._task:
            node._task.cancel()
            try:
                await node._task
            except asyncio.CancelledError:
                pass
            node._task = None
        logger.info(f"Stopped ESP32 node: {node_id}")

    async def start_all_nodes(self):
        for node_id in self._nodes:
            await self.start_node(node_id)

    async def stop_all_nodes(self):
        for node_id in list(self._nodes.keys()):
            await self.stop_node(node_id)

    async def _sensor_loop(self, node: ESP32Node):
        while node._running:
            try:
                for sensor_config in self._sensor_configs:
                    current_val = node.sensors.get(sensor_config.identifier, sensor_config.default_value)
                    change = random.uniform(-sensor_config.variance, sensor_config.variance)
                    new_val = max(sensor_config.min_value, min(sensor_config.max_value, current_val + change))
                    new_val = round(new_val, sensor_config.decimal_places)
                    node.update_sensor_value(sensor_config.identifier, new_val)
                
                node.last_heartbeat = datetime.utcnow()
                await asyncio.sleep(node.sampling_interval)
            except Exception as e:
                logger.exception(f"Sensor loop error for node {node.node_id}: {e}")

    async def send_command(self, node_id: str, command: str, params: dict):
        node = self._nodes.get(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")
        
        if command == "set_fan":
            node.set_actuator_state("fan_status", params.get("status", False))
        elif command == "set_light":
            node.set_actuator_state("light_status", params.get("status", False))
            if "brightness" in params:
                node.sensors["brightness"] = params["brightness"]
        elif command == "set_pump":
            node.set_actuator_state("pump_status", params.get("status", False))
        elif command == "set_mode":
            node.sensors["work_mode"] = params.get("mode", "manual")
        elif command == "raw_command":
            logger.info(f"[{node.node_name}] Raw command: {params}")
        else:
            logger.warning(f"Unknown command: {command}")
        
        return {"success": True, "node_id": node_id}

    def get_node_status(self, node_id: str) -> Optional[Dict]:
        node = self._nodes.get(node_id)
        if not node:
            return None
        
        return {
            "node_id": node.node_id,
            "node_name": node.node_name,
            "product_key": node.product_key,
            "status": node.status,
            "last_heartbeat": node.last_heartbeat.isoformat() if node.last_heartbeat else None,
            "sensors": node.sensors,
            "actuators": node.actuators,
            "sampling_interval": node.sampling_interval,
        }


esp32_simulator_manager = ESP32SimulatorManager()