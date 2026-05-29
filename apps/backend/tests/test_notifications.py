"""Tests for Fix 22: queue_notification must send real SMS via Fast2SMS when channel='sms'."""
from unittest.mock import MagicMock, patch

import pytest


class TestQueueNotificationSms:
    """Fix 22: queue_notification dispatches to Fast2SMS when channel='sms'."""

    def test_queue_notification_calls_send_sms_for_sms_channel(self):
        """When channel='sms' and a recipient is supplied, send_sms must be called once."""
        from app.services.notification_service import queue_notification

        with patch("app.services.notification_service.send_sms") as mock_sms, \
             patch("app.services.notification_service.audit_event"):
            queue_notification(
                channel="sms",
                recipient="9876543210",
                template="Your worker has been assigned.",
                context={"message": "Your job is confirmed."},
            )

        mock_sms.assert_called_once_with("9876543210", "Your job is confirmed.")

    def test_queue_notification_uses_template_when_message_not_in_context(self):
        """When context has no 'message' key, the template string is used as the SMS body."""
        from app.services.notification_service import queue_notification

        with patch("app.services.notification_service.send_sms") as mock_sms, \
             patch("app.services.notification_service.audit_event"):
            queue_notification(
                channel="sms",
                recipient="9876543210",
                template="Fallback template text",
                context={},
            )

        mock_sms.assert_called_once_with("9876543210", "Fallback template text")

    def test_queue_notification_does_not_call_send_sms_for_push_channel(self):
        """channel='push' must not trigger SMS."""
        from app.services.notification_service import queue_notification

        with patch("app.services.notification_service.send_sms") as mock_sms, \
             patch("app.services.notification_service.audit_event"):
            queue_notification(
                channel="push",
                recipient="9876543210",
                template="Push notification body",
                context={},
            )

        mock_sms.assert_not_called()

    def test_queue_notification_does_not_call_send_sms_when_recipient_is_empty(self):
        """An empty recipient must not trigger SMS (guard against blank phone numbers)."""
        from app.services.notification_service import queue_notification

        with patch("app.services.notification_service.send_sms") as mock_sms, \
             patch("app.services.notification_service.audit_event"):
            queue_notification(
                channel="sms",
                recipient="",
                template="Some message",
                context={},
            )

        mock_sms.assert_not_called()

    def test_send_sms_skips_when_api_key_not_configured(self, monkeypatch):
        """send_sms must log a warning and return gracefully when FAST2SMS_API_KEY is blank."""
        import app.services.notification_service as ns

        monkeypatch.setattr(ns.settings, "fast2sms_api_key", "")
        monkeypatch.setenv("APP_ENV", "staging")
        monkeypatch.setattr(ns.settings, "app_env", "staging")

        with patch("app.services.notification_service.logger") as mock_logger:
            ns.send_sms("9876543210", "Test message")

        mock_logger.warning.assert_called_once()

    def test_send_sms_calls_fast2sms_api(self, monkeypatch):
        """send_sms must POST to Fast2SMS with the correct headers and params."""
        import app.services.notification_service as ns

        monkeypatch.setattr(ns.settings, "fast2sms_api_key", "test-api-key")
        # Override is_local so the dev guard does not short-circuit in test env
        monkeypatch.setenv("APP_ENV", "staging")
        monkeypatch.setattr(ns.settings, "app_env", "staging")

        mock_response = MagicMock()
        mock_response.json.return_value = {"return": True}

        with patch("httpx.Client") as mock_client_cls:
            mock_http = MagicMock()
            mock_http.get.return_value = mock_response
            mock_client_cls.return_value.__enter__.return_value = mock_http

            ns.send_sms("9876543210", "Hello worker")

        mock_http.get.assert_called_once()
        call_kwargs = mock_http.get.call_args
        assert call_kwargs[0][0] == ns._FAST2SMS_URL
        assert call_kwargs[1]["headers"]["authorization"] == "test-api-key"
        assert call_kwargs[1]["params"]["numbers"] == "9876543210"
        assert call_kwargs[1]["params"]["message"] == "Hello worker"
