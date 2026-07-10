import logging
import json
from typing import Dict, Any
from datetime import datetime

from ..models.models import AlertEvent, AlertSeverity

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self._channels = {}

    def register_channel(self, name: str, handler):
        self._channels[name] = handler
        logger.info(f"Notification channel registered: {name}")

    async def send_notification(self, event: AlertEvent, config: Dict[str, Any]):
        if not config:
            return

        for channel_name, channel_config in config.items():
            handler = self._channels.get(channel_name)
            if handler:
                try:
                    await handler(event, channel_config)
                except Exception as e:
                    logger.error(f"Failed to send notification via {channel_name}: {e}")

    async def send_all(self, event: AlertEvent, channels: Dict[str, Any] = None):
        if not channels:
            channels = {"system": {}}
        await self.send_notification(event, channels)


class SystemNotificationHandler:
    async def __call__(self, event: AlertEvent, config: Dict[str, Any]):
        logger.info(f"[System Notification] Alert: {event.message}")


class WebhookNotificationHandler:
    async def __call__(self, event: AlertEvent, config: Dict[str, Any]):
        url = config.get("url")
        if not url:
            return

        try:
            import aiohttp
            payload = {
                "event_id": event.id,
                "message": event.message,
                "severity": event.severity.value,
                "device_id": event.device_id,
                "property": event.property_identifier,
                "current_value": event.current_value,
                "threshold": event.threshold_value,
                "operator": event.operator,
                "status": event.status.value,
                "created_at": event.created_at.isoformat() if event.created_at else None,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status != 200:
                        logger.error(f"Webhook failed: HTTP {response.status}")
                    else:
                        logger.info(f"Webhook sent successfully to {url}")
        except Exception as e:
            logger.error(f"Webhook error: {e}")


class EmailNotificationHandler:
    async def __call__(self, event: AlertEvent, config: Dict[str, Any]):
        to_email = config.get("to")
        smtp_config = config.get("smtp", {})

        if not to_email:
            return

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            subject = f"[告警] {event.message}"
            body = f"""告警信息：
告警ID: {event.id}
消息: {event.message}
级别: {self._get_severity_text(event.severity)}
设备ID: {event.device_id}
属性: {event.property_identifier}
当前值: {event.current_value}
阈值: {event.threshold_value}
操作符: {event.operator}
状态: {event.status.value}
时间: {event.created_at}
"""

            msg = MIMEMultipart()
            msg['From'] = smtp_config.get('from', 'alerts@iot-platform.local')
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            smtp_server = smtp_config.get('server', 'localhost')
            smtp_port = smtp_config.get('port', 25)
            smtp_user = smtp_config.get('user')
            smtp_password = smtp_config.get('password')

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)
                logger.info(f"Email sent to {to_email}")
        except Exception as e:
            logger.error(f"Email notification error: {e}")

    def _get_severity_text(self, severity: AlertSeverity) -> str:
        mapping = {
            AlertSeverity.INFO: "信息",
            AlertSeverity.WARNING: "警告",
            AlertSeverity.ERROR: "错误",
            AlertSeverity.CRITICAL: "严重",
        }
        return mapping.get(severity, severity.value)


class DingTalkNotificationHandler:
    async def __call__(self, event: AlertEvent, config: Dict[str, Any]):
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            return

        try:
            import aiohttp

            payload = {
                "msgtype": "text",
                "text": {
                    "content": f"【告警通知】\n{event.message}\n\n设备ID: {event.device_id}\n级别: {self._get_severity_text(event.severity)}\n当前值: {event.current_value}\n阈值: {event.threshold_value}"
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, timeout=10) as response:
                    if response.status != 200:
                        logger.error(f"DingTalk webhook failed: HTTP {response.status}")
                    else:
                        logger.info(f"DingTalk message sent successfully")
        except Exception as e:
            logger.error(f"DingTalk notification error: {e}")

    def _get_severity_text(self, severity: AlertSeverity) -> str:
        mapping = {
            AlertSeverity.INFO: "信息",
            AlertSeverity.WARNING: "警告",
            AlertSeverity.ERROR: "错误",
            AlertSeverity.CRITICAL: "严重",
        }
        return mapping.get(severity, severity.value)


notification_service = NotificationService()
notification_service.register_channel("system", SystemNotificationHandler())
notification_service.register_channel("webhook", WebhookNotificationHandler())
notification_service.register_channel("email", EmailNotificationHandler())
notification_service.register_channel("dingtalk", DingTalkNotificationHandler())