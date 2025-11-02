"""
Email service for sending verification emails and notifications.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails."""

    def __init__(self):
        self.settings = get_settings()

    async def send_verification_email(self, email: str, verification_token: str):
        """Send email verification email."""
        logger.info(f"📧 Starting email verification process for: {email}")
        logger.info(f"SMTP Server configured: {self.settings.SMTP_SERVER}")
        logger.info(f"SMTP Port: {self.settings.SMTP_PORT}")
        logger.info(f"SMTP Username: {self.settings.SMTP_USERNAME}")
        logger.info(f"SMTP TLS: {self.settings.SMTP_USE_TLS}")
        
        if not self.settings.SMTP_SERVER:
            logger.warning("SMTP not configured, using development email simulation")
            await self._simulate_email_for_development(email, verification_token)
            return
            
        logger.info("SMTP is configured, attempting to send real email...")

        subject = "Verify Your Email - WorldClass Video"
        verification_url = (
            f"http://localhost:3000/verify-email?token={verification_token}"
        )

        html_content = f"""
        <html>
        <body>
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #333;">Welcome to WorldClass Video!</h2>
                <p>Thank you for registering! Please verify your email address using one of the methods below:</p>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #007bff; margin-top: 0;">Option 1: Click the Verification Button</h3>
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="{verification_url}" 
                           style="background-color: #007bff; color: white; padding: 12px 30px; 
                                  text-decoration: none; border-radius: 5px; font-weight: bold;">
                            Verify Email Address
                        </a>
                    </div>
                </div>
                
                <div style="background-color: #e9ecef; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #007bff; margin-top: 0;">Option 2: Enter Verification Code</h3>
                    <p>If you prefer to enter a code manually, use this verification code:</p>
                    <div style="background-color: white; padding: 15px; border-radius: 5px; text-align: center; font-family: monospace; font-size: 18px; font-weight: bold; letter-spacing: 2px; margin: 10px 0;">
                        {verification_token}
                    </div>
                    <p style="font-size: 12px; color: #666;">Copy and paste this code into the verification form on the website.</p>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #007bff; font-size: 12px;">{verification_url}</p>
                
                <p style="margin-top: 30px; color: #666; font-size: 12px;">
                    This verification will expire in 24 hours. 
                    If you didn't create an account, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Welcome to WorldClass Video!
        
        Thank you for registering! Please verify your email address using one of these methods:
        
        OPTION 1: Click this link
        {verification_url}
        
        OPTION 2: Enter this verification code on the website
        {verification_token}
        
        This verification will expire in 24 hours.
        If you didn't create an account, please ignore this email.
        """

        await self._send_email(email, subject, html_content, text_content)

    async def send_meeting_invitation(
        self, email: str, meeting_title: str, meeting_url: str, meeting_time: str
    ):
        """Send meeting invitation email."""
        if not self.settings.SMTP_SERVER:
            logger.warning("SMTP not configured, skipping meeting invitation")
            return

        subject = f"Meeting Invitation: {meeting_title}"

        html_content = f"""
        <html>
        <body>
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #333;">You're Invited to a Meeting</h2>
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #007bff;">{meeting_title}</h3>
                    <p><strong>Time:</strong> {meeting_time}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{meeting_url}" 
                       style="background-color: #28a745; color: white; padding: 12px 30px; 
                              text-decoration: none; border-radius: 5px; font-weight: bold;">
                        Join Meeting
                    </a>
                </div>
                
                <p>Or copy and paste this link into your browser:</p>
                <p style="word-break: break-all; color: #007bff;">{meeting_url}</p>
                
                <p style="margin-top: 30px; color: #666; font-size: 12px;">
                    This invitation was sent by WorldClass Video platform.
                </p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        You're Invited to a Meeting
        
        Meeting: {meeting_title}
        Time: {meeting_time}
        
        Join the meeting by visiting this link:
        {meeting_url}
        """

        await self._send_email(email, subject, html_content, text_content)

    async def _send_email(
        self, to_email: str, subject: str, html_content: str, text_content: str
    ):
        """Send email using SMTP."""
        logger.info(f"📨 Preparing to send email to: {to_email}")
        logger.info(f"Subject: {subject}")
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            from_email = (
                getattr(self.settings, 'FROM_EMAIL', None)
                or self.settings.SMTP_USERNAME
            )
            msg["From"] = from_email
            msg["To"] = to_email
            
            logger.info(f"From email: {from_email}")
            logger.info(
                f"SMTP connection: {self.settings.SMTP_SERVER}:"
                f"{self.settings.SMTP_PORT}"
            )

            # Create text and HTML parts
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")

            msg.attach(text_part)
            msg.attach(html_part)

            # Send email
            logger.info("🔗 Attempting SMTP connection...")
            with smtplib.SMTP(
                self.settings.SMTP_SERVER, self.settings.SMTP_PORT
            ) as server:
                logger.info("✅ SMTP connection established")
                
                if self.settings.SMTP_USE_TLS:
                    logger.info("🔒 Starting TLS...")
                    server.starttls()
                    logger.info("✅ TLS enabled successfully")

                if self.settings.SMTP_USERNAME and self.settings.SMTP_PASSWORD:
                    logger.info("🔐 Attempting SMTP authentication...")
                    server.login(
                        self.settings.SMTP_USERNAME, self.settings.SMTP_PASSWORD
                    )
                    logger.info("✅ SMTP authentication successful")

                logger.info("📤 Sending email message...")
                server.send_message(msg)
                logger.info("✅ Email message sent to SMTP server")

            logger.info(f"🎉 Email sent successfully to {to_email}")

        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            # Don't raise exception to avoid breaking the registration flow

    async def _simulate_email_for_development(
        self, email: str, verification_token: str
    ):
        """Simulate sending email for development."""
        verification_url = (
            f"http://localhost:3000/verify-email?token={verification_token}"
        )
        
        # Log to console
        print("\n" + "="*80)
        print("📧 DEVELOPMENT EMAIL SIMULATION")
        print("="*80)
        print(f"To: {email}")
        print("Subject: Verify Your Email - WorldClass Video")
        print(f"Verification Token: {verification_token}")
        print(f"Verification URL: {verification_url}")
        print("="*80)
        print("Copy the verification URL above and paste it in your browser")
        print("OR use the token directly in the verification form")
        print("="*80 + "\n")
        
        # Also save to a file for easy access
        try:
            import os
            dev_emails_dir = "dev_emails"
            if not os.path.exists(dev_emails_dir):
                os.makedirs(dev_emails_dir)
            
            with open(f"{dev_emails_dir}/latest_verification.txt", "w") as f:
                f.write(f"Email: {email}\n")
                f.write(f"Token: {verification_token}\n")
                f.write(f"URL: {verification_url}\n")
                from datetime import datetime
                f.write(f"Generated at: {datetime.now()}\n")
            
            logger.info(
                f"Development verification email info saved to "
                f"{dev_emails_dir}/latest_verification.txt"
            )
        except Exception as e:
            logger.warning(f"Could not save development email to file: {e}")
        
        logger.info(
            f"Verification email simulated for {email} - "
            "Check console output for details"
        )
