"""
Real Notification Service.

Implements actual delivery for:
- Slack (webhooks)
- Email (SMTP)
- Microsoft Teams (webhooks)
- Discord (webhooks)
- Generic webhooks
"""

import asyncio
import json
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import logging

# Use aiohttp for async HTTP if available, fall back to urllib
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    import urllib.request
    import urllib.error

logger = logging.getLogger(__name__)


async def send_slack_message(
    webhook_url: str,
    message: str,
    channel: Optional[str] = None,
    username: Optional[str] = "DevOps Hub",
    icon_emoji: Optional[str] = ":robot_face:",
    attachments: Optional[List[Dict]] = None,
    blocks: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Send a message to Slack via webhook.

    Args:
        webhook_url: Slack incoming webhook URL
        message: Text message to send
        channel: Optional channel override
        username: Bot username
        icon_emoji: Bot icon emoji
        attachments: Slack attachments
        blocks: Slack block kit blocks

    Returns:
        Dict with success status and any error message
    """
    if not webhook_url:
        return {"success": False, "error": "No webhook URL provided"}

    if not webhook_url.startswith("https://hooks.slack.com/"):
        logger.warning(f"Slack webhook URL doesn't look valid: {webhook_url[:50]}...")

    payload = {
        "text": message,
        "username": username,
        "icon_emoji": icon_emoji,
    }

    if channel:
        payload["channel"] = channel
    if attachments:
        payload["attachments"] = attachments
    if blocks:
        payload["blocks"] = blocks

    return await _send_http_post(webhook_url, payload, "Slack")


async def send_teams_message(
    webhook_url: str,
    message: str,
    title: Optional[str] = "DevOps Hub Notification",
    theme_color: Optional[str] = "0078D7",
) -> Dict[str, Any]:
    """
    Send a message to Microsoft Teams via webhook.

    Args:
        webhook_url: Teams incoming webhook URL
        message: Text message to send
        title: Card title
        theme_color: Card theme color (hex without #)

    Returns:
        Dict with success status and any error message
    """
    if not webhook_url:
        return {"success": False, "error": "No webhook URL provided"}

    # Teams uses Office 365 Connector Card format
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": theme_color,
        "summary": title,
        "sections": [{
            "activityTitle": title,
            "facts": [],
            "markdown": True,
            "text": message,
        }],
    }

    return await _send_http_post(webhook_url, payload, "Teams")


async def send_discord_message(
    webhook_url: str,
    message: str,
    username: Optional[str] = "DevOps Hub",
    avatar_url: Optional[str] = None,
    embeds: Optional[List[Dict]] = None,
) -> Dict[str, Any]:
    """
    Send a message to Discord via webhook.

    Args:
        webhook_url: Discord webhook URL
        message: Text message to send
        username: Bot username
        avatar_url: Bot avatar URL
        embeds: Discord embeds

    Returns:
        Dict with success status and any error message
    """
    if not webhook_url:
        return {"success": False, "error": "No webhook URL provided"}

    payload = {
        "content": message,
        "username": username,
    }

    if avatar_url:
        payload["avatar_url"] = avatar_url
    if embeds:
        payload["embeds"] = embeds

    return await _send_http_post(webhook_url, payload, "Discord")


async def send_webhook(
    url: str,
    payload: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    method: str = "POST",
) -> Dict[str, Any]:
    """
    Send a generic webhook request.

    Args:
        url: Webhook URL
        payload: JSON payload
        headers: Optional additional headers
        method: HTTP method (POST, PUT, PATCH)

    Returns:
        Dict with success status, response data, and any error message
    """
    if not url:
        return {"success": False, "error": "No URL provided"}

    return await _send_http_post(url, payload, "Webhook", extra_headers=headers)


async def send_email(
    smtp_host: str,
    smtp_port: int,
    username: str,
    password: str,
    from_address: str,
    to_addresses: List[str],
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    use_tls: bool = True,
    from_name: Optional[str] = "DevOps Hub",
) -> Dict[str, Any]:
    """
    Send an email via SMTP.

    Args:
        smtp_host: SMTP server hostname
        smtp_port: SMTP server port
        username: SMTP username
        password: SMTP password
        from_address: Sender email address
        to_addresses: List of recipient email addresses
        subject: Email subject
        body: Plain text body
        html_body: Optional HTML body
        use_tls: Whether to use TLS
        from_name: Sender display name

    Returns:
        Dict with success status and any error message
    """
    if not smtp_host or not to_addresses:
        return {"success": False, "error": "Missing SMTP host or recipients"}

    try:
        # Create message
        if html_body:
            msg = MIMEMultipart("alternative")
            msg.attach(MIMEText(body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
        else:
            msg = MIMEText(body, "plain")

        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{from_address}>" if from_name else from_address
        msg["To"] = ", ".join(to_addresses)

        # Send via SMTP
        # Run in thread pool to not block async loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            _send_smtp_sync,
            smtp_host,
            smtp_port,
            username,
            password,
            from_address,
            to_addresses,
            msg,
            use_tls,
        )

        logger.info(f"Email sent to {len(to_addresses)} recipients")
        return {"success": True, "recipients": len(to_addresses)}

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed: {e}")
        return {"success": False, "error": "SMTP authentication failed"}
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return {"success": False, "error": f"SMTP error: {str(e)}"}
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return {"success": False, "error": str(e)}


def _send_smtp_sync(
    host: str,
    port: int,
    username: str,
    password: str,
    from_addr: str,
    to_addrs: List[str],
    msg: MIMEText,
    use_tls: bool,
):
    """Synchronous SMTP send for use in thread pool."""
    context = ssl.create_default_context()

    if use_tls:
        with smtplib.SMTP(host, port) as server:
            server.starttls(context=context)
            if username and password:
                server.login(username, password)
            server.sendmail(from_addr, to_addrs, msg.as_string())
    else:
        with smtplib.SMTP_SSL(host, port, context=context) as server:
            if username and password:
                server.login(username, password)
            server.sendmail(from_addr, to_addrs, msg.as_string())


async def _send_http_post(
    url: str,
    payload: Dict[str, Any],
    service_name: str,
    extra_headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Send an HTTP POST request with JSON payload.

    Uses aiohttp if available, falls back to urllib.
    """
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "DevOps-Hub/1.0",
    }
    if extra_headers:
        headers.update(extra_headers)

    json_data = json.dumps(payload).encode("utf-8")

    if HAS_AIOHTTP:
        return await _send_with_aiohttp(url, json_data, headers, service_name)
    else:
        return await _send_with_urllib(url, json_data, headers, service_name)


async def _send_with_aiohttp(
    url: str,
    data: bytes,
    headers: Dict[str, str],
    service_name: str,
) -> Dict[str, Any]:
    """Send request using aiohttp."""
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, data=data, headers=headers) as response:
                response_text = await response.text()

                if response.status in (200, 201, 202, 204):
                    logger.info(f"{service_name} notification sent successfully")
                    return {
                        "success": True,
                        "status_code": response.status,
                        "response": response_text[:500] if response_text else None,
                    }
                else:
                    logger.warning(f"{service_name} returned status {response.status}: {response_text[:200]}")
                    return {
                        "success": False,
                        "status_code": response.status,
                        "error": f"HTTP {response.status}: {response_text[:200]}",
                    }

    except asyncio.TimeoutError:
        logger.error(f"{service_name} request timed out")
        return {"success": False, "error": "Request timed out"}
    except aiohttp.ClientError as e:
        logger.error(f"{service_name} request failed: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"{service_name} unexpected error: {e}")
        return {"success": False, "error": str(e)}


async def _send_with_urllib(
    url: str,
    data: bytes,
    headers: Dict[str, str],
    service_name: str,
) -> Dict[str, Any]:
    """Send request using urllib (fallback)."""
    loop = asyncio.get_event_loop()

    def _do_request():
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.status, response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", errors="replace")

    try:
        status, response_text = await loop.run_in_executor(None, _do_request)

        if status in (200, 201, 202, 204):
            logger.info(f"{service_name} notification sent successfully")
            return {
                "success": True,
                "status_code": status,
                "response": response_text[:500] if response_text else None,
            }
        else:
            logger.warning(f"{service_name} returned status {status}: {response_text[:200]}")
            return {
                "success": False,
                "status_code": status,
                "error": f"HTTP {status}: {response_text[:200]}",
            }

    except urllib.error.URLError as e:
        logger.error(f"{service_name} request failed: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"{service_name} unexpected error: {e}")
        return {"success": False, "error": str(e)}


class NotificationManager:
    """
    High-level notification manager that routes notifications
    based on user preferences and configured integrations.
    """

    def __init__(self):
        from core.integrations import (
            get_integration_repository,
            get_credential_repository,
            get_user_settings_repository,
            IntegrationType,
            CredentialType,
        )
        self.int_repo = get_integration_repository()
        self.cred_repo = get_credential_repository()
        self.settings_repo = get_user_settings_repository()

    async def send_notification(
        self,
        event_type: str,
        title: str,
        message: str,
        api_key_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send notification through all enabled channels.

        Args:
            event_type: Type of event (workflow_completed, agent_error, etc.)
            title: Notification title
            message: Notification message
            api_key_id: Owner's API key for preferences lookup
            data: Additional data to include

        Returns:
            Dict with results from each channel
        """
        from core.integrations import IntegrationType, CredentialType

        # Get user preferences
        prefs = self.settings_repo.get_notification_preferences(api_key_id or "__default__")

        if not prefs.get("enabled", True):
            return {"skipped": True, "reason": "Notifications disabled"}

        # Check if this event type is enabled
        if not prefs.get("events", {}).get(event_type, True):
            return {"skipped": True, "reason": f"Event type {event_type} disabled"}

        results = {}
        channels = prefs.get("channels", {})

        # Get all active integrations
        integrations = self.int_repo.list_all_active()

        for integration in integrations:
            channel_name = integration.type.value

            # Check if channel is enabled in preferences
            if not channels.get(channel_name, False):
                continue

            try:
                if integration.type == IntegrationType.SLACK:
                    webhook_url = self.cred_repo.retrieve(integration.id, CredentialType.WEBHOOK_URL)
                    if webhook_url:
                        result = await send_slack_message(
                            webhook_url=webhook_url,
                            message=f"*{title}*\n{message}",
                            channel=integration.config.get("default_channel"),
                            username=integration.config.get("bot_name", "DevOps Hub"),
                            icon_emoji=integration.config.get("icon_emoji", ":robot_face:"),
                        )
                        results[f"slack_{integration.name}"] = result
                        self.int_repo.update_last_used(
                            integration.id,
                            error=None if result["success"] else result.get("error")
                        )

                elif integration.type == IntegrationType.TEAMS:
                    webhook_url = self.cred_repo.retrieve(integration.id, CredentialType.WEBHOOK_URL)
                    if webhook_url:
                        result = await send_teams_message(
                            webhook_url=webhook_url,
                            message=message,
                            title=title,
                        )
                        results[f"teams_{integration.name}"] = result
                        self.int_repo.update_last_used(
                            integration.id,
                            error=None if result["success"] else result.get("error")
                        )

                elif integration.type == IntegrationType.DISCORD:
                    webhook_url = self.cred_repo.retrieve(integration.id, CredentialType.WEBHOOK_URL)
                    if webhook_url:
                        result = await send_discord_message(
                            webhook_url=webhook_url,
                            message=f"**{title}**\n{message}",
                        )
                        results[f"discord_{integration.name}"] = result
                        self.int_repo.update_last_used(
                            integration.id,
                            error=None if result["success"] else result.get("error")
                        )

                elif integration.type == IntegrationType.WEBHOOK:
                    webhook_url = self.cred_repo.retrieve(integration.id, CredentialType.WEBHOOK_URL)
                    if webhook_url:
                        result = await send_webhook(
                            url=webhook_url,
                            payload={
                                "event": event_type,
                                "title": title,
                                "message": message,
                                "timestamp": datetime.utcnow().isoformat(),
                                "data": data or {},
                            },
                        )
                        results[f"webhook_{integration.name}"] = result
                        self.int_repo.update_last_used(
                            integration.id,
                            error=None if result["success"] else result.get("error")
                        )

            except Exception as e:
                logger.error(f"Failed to send to {integration.name}: {e}")
                results[f"{channel_name}_{integration.name}"] = {
                    "success": False,
                    "error": str(e),
                }

        return results


# Global notification manager instance
_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """Get the notification manager instance."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager
