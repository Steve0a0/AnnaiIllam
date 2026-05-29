"""
Notification service.

Push notifications are sent via the Expo Push API (free, no key required for
Expo-hosted tokens starting with "ExponentPushToken[...").

`send_push_to_user` — look up all active tokens for a user, fire push messages.
`enqueue_push_to_user` — non-blocking variant: schedules the push via FastAPI
                         BackgroundTasks so the HTTP response is not delayed.
`queue_notification` — sends SMS via Fast2SMS when channel="sms"; always audits.
"""

import logging
from typing import Any

import httpx
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.push_token_repository import get_active_push_tokens_for_user
from app.utils.audit import audit_event

logger = logging.getLogger(__name__)

_FAST2SMS_URL = "https://www.fast2sms.com/dev/bulkV2"

_EXPO_PUSH_URL = "https://exp.host/push/send"
_EXPO_HEADERS = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip, deflate",
    "Content-Type": "application/json",
}


def send_push_to_user(
    db: Session,
    *,
    user_id: int,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
) -> None:
    """
    Send a push notification to every active device registered for `user_id`.
    Failures are logged but never raised — a push failure must never break the
    calling request.
    """
    tokens = get_active_push_tokens_for_user(db, user_id)
    if not tokens:
        return

    messages = [
        {
            "to": token,
            "title": title,
            "body": body,
            "data": data or {},
            "sound": "default",
            "priority": "high",
        }
        for token in tokens
    ]

    try:
        with httpx.Client(timeout=5) as client:
            response = client.post(_EXPO_PUSH_URL, headers=_EXPO_HEADERS, json=messages)
            response.raise_for_status()
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send push notification to user_id=%s", user_id)


def enqueue_push_to_user(
    background_tasks: BackgroundTasks,
    db: Session,
    *,
    user_id: int,
    title: str,
    body: str,
    data: dict[str, Any] | None = None,
) -> None:
    """
    Non-blocking: schedules `send_push_to_user` as a FastAPI background task.
    Use this in route handlers so the HTTP response is returned immediately.
    """
    background_tasks.add_task(
        send_push_to_user,
        db,
        user_id=user_id,
        title=title,
        body=body,
        data=data,
    )


def send_sms(phone: str, message: str) -> None:
    """Send a transactional SMS via Fast2SMS quick route.
    Failures are logged but never raised — an SMS failure must never break the caller.
    No-ops in local/dev mode so tests never call the real gateway.
    """
    if settings.is_local:
        logger.debug("[DEV] SMS to %s: %s", phone, message)
        return
    api_key = settings.fast2sms_api_key
    if not api_key:
        logger.warning("FAST2SMS_API_KEY not configured — SMS not sent to %s", phone)
        return
    try:
        with httpx.Client(timeout=10) as client:
            resp = client.get(
                _FAST2SMS_URL,
                headers={"authorization": api_key},
                params={
                    "route": "q",
                    "message": message,
                    "language": "english",
                    "flash": 0,
                    "numbers": phone,
                },
            )
            resp.raise_for_status()
            body = resp.json()
            if not body.get("return", False):
                raise RuntimeError(f"Fast2SMS error: {body.get('message', body)}")
            logger.info("SMS sent via Fast2SMS | phone=%s", phone)
    except Exception:  # noqa: BLE001
        logger.exception("Failed to send SMS to phone=%s", phone)


def queue_notification(
    *,
    channel: str,
    recipient: str,
    template: str,
    context: dict,
) -> None:
    """Send a notification and audit the event.
    When channel='sms', dispatches a real SMS via Fast2SMS.
    """
    audit_event(
        "notification_queued",
        {
            "channel": channel,
            "recipient": recipient,
            "template": template,
            "context": context,
        },
    )
    if channel == "sms" and recipient:
        message = context.get("message") or template
        send_sms(recipient, message)
