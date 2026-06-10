import asyncio
import json
from gmqtt import Client as MQTTClient
from ..config import settings
from .handler import MQTTHandler


class MQTTService:
    def __init__(self):
        self.client: MQTTClient = None
        self.handler: MQTTHandler = None
        self._connected = False

    async def start(self, db_session_factory):
        """启动MQTT服务"""
        self.client = MQTTClient("iot_platform_backend")
        self.handler = MQTTHandler(db_session_factory)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        try:
            await self.client.connect(settings.MQTT_BROKER_URL, settings.MQTT_BROKER_PORT, timeout=5)
            self._connected = True
            print(f"Connected to MQTT broker at {settings.MQTT_BROKER_URL}:{settings.MQTT_BROKER_PORT}")
        except Exception as e:
            print(f"Warning: Could not connect to MQTT broker at {settings.MQTT_BROKER_URL}:{settings.MQTT_BROKER_PORT} - {e}")
            print("MQTT functionality will be unavailable. The application will continue without MQTT support.")
            self._connected = False

    def _on_connect(self, client, flags, rc, properties):
        print("MQTT client connected")
        # 订阅设备主题
        client.subscribe("devices/+/telemetry")
        client.subscribe("devices/+/status")
        client.subscribe("devices/+/events")
        client.subscribe("devices/+/commands/response")

    async def _on_message(self, client, topic, payload, qos, properties):
        try:
            # 解析topic: devices/{device_key}/{type}
            parts = topic.split("/")
            if len(parts) >= 3:
                device_key = parts[1]
                msg_type = parts[2]

                payload_dict = json.loads(payload.decode())
                if msg_type == "telemetry":
                    await self.handler.handle_telemetry(device_key, payload_dict)
                elif msg_type == "status":
                    await self.handler.handle_status(device_key, payload_dict)
                elif msg_type == "events":
                    await self.handler.handle_event(device_key, payload_dict)
                elif msg_type == "commands" and len(parts) > 3 and parts[3] == "response":
                    await self.handler.handle_command_response(device_key, payload_dict)
        except Exception as e:
            print(f"Error handling MQTT message: {e}")

    def _on_disconnect(self, client, packet, exc=None):
        print("MQTT client disconnected")
        self._connected = False

    async def publish_command(self, device_key: str, command_id: str, service_identifier: str, parameters: dict):
        """发布命令到设备"""
        if not self._connected:
            print("MQTT client not connected, cannot publish command")
            return False

        from datetime import datetime
        topic = f"devices/{device_key}/commands"
        payload = {
            "command_id": command_id,
            "service_identifier": service_identifier,
            "parameters": parameters,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.client.publish(topic, json.dumps(payload))
        return True

    async def stop(self):
        """停止MQTT服务"""
        if self.client and self._connected:
            await self.client.disconnect()


mqtt_service = MQTTService()
