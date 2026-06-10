import json
import asyncio
from datetime import datetime


class MQTTService:
    def __init__(self):
        self.client = None
        self.handler = None
        self._connected = False
        self._db_session_factory = None

    async def start(self, db_session_factory):
        """启动 MQTT 服务（不依赖 broker，仅初始化处理对象，支持手动发布）"""
        self._db_session_factory = db_session_factory
        from .handler import MQTTHandler
        self.handler = MQTTHandler(db_session_factory)

        # 尝试连接 broker（如果可用）
        try:
            from gmqtt import Client as MQTTClient
            from ..config import settings
            if settings.MQTT_BROKER_URL:
                self.client = MQTTClient(f"iot-platform-backend-{datetime.now().strftime('%Y%m%d%H%M%S')}")
                self.client.on_connect = self._on_connect
                self.client.on_message = self._on_message
                self.client.on_disconnect = self._on_disconnect
                await self.client.connect(settings.MQTT_BROKER_URL, settings.MQTT_BROKER_PORT or 1883)
                self._connected = True
                print(f"[MQTT] Connected to {settings.MQTT_BROKER_URL}:{settings.MQTT_BROKER_PORT}")
        except Exception as e:
            print(f"[MQTT] Broker not available ({e}). Commands will still be saved to database.")
            self._connected = False

    def _on_connect(self, client, flags, rc, properties):
        self._connected = True
        topics = [
            "devices/+/telemetry",
            "devices/+/status",
            "devices/+/events",
            "devices/+/commands/response",
        ]
        for topic in topics:
            client.subscribe(topic, qos=1)
        print(f"[MQTT] Subscribed to {len(topics)} topics")

    async def _on_message(self, client, topic, payload, qos, properties):
        try:
            parts = topic.split("/")
            if len(parts) >= 3 and parts[0] == "devices":
                device_key = parts[1]
                msg_type = parts[2]
                data = json.loads(payload.decode()) if isinstance(payload, (bytes, bytearray)) else payload

                if msg_type == "telemetry":
                    await self.handler.handle_telemetry(device_key, data)
                elif msg_type == "status":
                    await self.handler.handle_status(device_key, data)
                elif msg_type == "events":
                    await self.handler.handle_event(device_key, data)
                elif msg_type == "commands" and len(parts) > 3 and parts[3] == "response":
                    await self.handler.handle_command_response(device_key, data)
        except Exception as e:
            print(f"[MQTT] Error handling message on {topic}: {e}")

    def _on_disconnect(self, client, packet, exc=None):
        self._connected = False
        print("[MQTT] Disconnected")

    async def publish_command(self, device_key: str, command_id: str, service_identifier: str, parameters: dict):
        """发布命令到设备（如果 broker 连接正常）"""
        if not self._connected or self.client is None:
            return False
        try:
            topic = f"devices/{device_key}/commands"
            payload = {
                "command_id": command_id,
                "service_identifier": service_identifier,
                "input_params": parameters,
                "timestamp": datetime.utcnow().isoformat(),
            }
            self.client.publish(topic, json.dumps(payload))
            return True
        except Exception as e:
            print(f"[MQTT] Failed to publish command: {e}")
            return False

    async def stop(self):
        if self.client and self._connected:
            try:
                await self.client.disconnect()
            except Exception:
                pass
            self._connected = False


mqtt_service = MQTTService()
