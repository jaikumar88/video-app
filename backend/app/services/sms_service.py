"""
SMS service for sending verification codes via Twilio.
"""

import logging
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)

try:
    from twilio.rest import Client

    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logger.warning("Twilio not installed. SMS functionality disabled.")


class SMSService:
    """Service for sending SMS messages."""

    def __init__(self):
        self.settings = get_settings()
        self.client = None

        if (
            TWILIO_AVAILABLE
            and self.settings.TWILIO_ACCOUNT_SID
            and self.settings.TWILIO_AUTH_TOKEN
        ):
            self.client = Client(
                self.settings.TWILIO_ACCOUNT_SID, self.settings.TWILIO_AUTH_TOKEN
            )

    async def send_verification_sms(self, phone_number: str, verification_code: str):
        """Send SMS verification code."""
        if not self.client:
            logger.warning("Twilio not configured, skipping SMS verification")
            return

        message_body = f"""
WorldClass Video Verification

Your verification code is: {verification_code}

This code will expire in 24 hours.
        """.strip()

        try:
            message = self.client.messages.create(
                body=message_body,
                from_=self.settings.TWILIO_PHONE_NUMBER,
                to=phone_number,
            )

            logger.info(f"SMS sent successfully to {phone_number}. SID: {message.sid}")

        except Exception as e:
            logger.error(f"Failed to send SMS to {phone_number}: {str(e)}")
            # Don't raise exception to avoid breaking the registration flow

    async def send_meeting_reminder_sms(
        self, phone_number: str, meeting_title: str, meeting_url: str, meeting_time: str
    ):
        """Send meeting reminder SMS."""
        if not self.client:
            logger.warning("Twilio not configured, skipping SMS reminder")
            return

        message_body = f"""
WorldClass Video Meeting Reminder

Meeting: {meeting_title}
Time: {meeting_time}

Join: {meeting_url}
        """.strip()

        try:
            message = self.client.messages.create(
                body=message_body,
                from_=self.settings.TWILIO_PHONE_NUMBER,
                to=phone_number,
            )

            logger.info(
                f"Meeting reminder SMS sent to {phone_number}. SID: {message.sid}"
            )

        except Exception as e:
            logger.error(
                f"Failed to send meeting reminder SMS to {phone_number}: {str(e)}"
            )
