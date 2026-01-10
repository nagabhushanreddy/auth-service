"""Notification service for email and SMS delivery"""
from typing import Optional, Dict, Any
from utils import logger
from app.config import settings


class EmailTemplates:
    """Email templates for various notifications"""
    
    @staticmethod
    def otp_email(otp: str, expires_in: str = "5 minutes") -> tuple:
        """OTP email template"""
        subject = "Your One-Time Password (OTP)"
        body = f"""
Hello,

Your One-Time Password (OTP) is: {otp}

This code expires in {expires_in}.

Do not share this code with anyone.

If you did not request this code, please ignore this email.

Best regards,
Multi-Finance Team
"""
        return subject, body
    
    @staticmethod
    def password_reset_email(reset_link: str, expires_in: str = "1 hour") -> tuple:
        """Password reset email template"""
        subject = "Password Reset Request"
        body = f"""
Hello,

We received a request to reset your password. Click the link below to proceed:

{reset_link}

This link expires in {expires_in}.

If you did not request this, please ignore this email.

Best regards,
Multi-Finance Team
"""
        return subject, body
    
    @staticmethod
    def account_locked_email() -> tuple:
        """Account locked email template"""
        subject = "Account Locked"
        body = """
Hello,

Your account has been locked due to multiple failed login attempts.

It will be automatically unlocked in 15 minutes. If you believe this is an error, 
please contact our support team.

Best regards,
Multi-Finance Team
"""
        return subject, body
    
    @staticmethod
    def welcome_email(username: str) -> tuple:
        """Welcome email template"""
        subject = "Welcome to Multi-Finance"
        body = f"""
Hello {username},

Welcome to Multi-Finance! Your account has been successfully created.

You can now log in using your credentials.

If you have any questions, feel free to contact our support team.

Best regards,
Multi-Finance Team
"""
        return subject, body


class NotificationService:
    """Notification service for email and SMS delivery"""
    
    @staticmethod
    async def send_otp(
        recipient: str,
        otp: str,
        method: str = "email"
    ) -> None:
        """Send OTP via email or SMS"""
        try:
            if method == "email":
                subject, body = EmailTemplates.otp_email(otp)
                await NotificationService.send_email(
                    to=recipient,
                    subject=subject,
                    body=body
                )
            elif method == "sms":
                await NotificationService.send_sms(
                    phone=recipient,
                    message=f"Your OTP is: {otp}. Valid for 5 minutes."
                )
            else:
                logger.warning(f"Unknown notification method: {method}")
        except Exception as e:
            logger.error(f"Failed to send OTP to {recipient} via {method}: {e}")
            raise
    
    @staticmethod
    async def send_password_reset_email(
        email: str,
        reset_link: str
    ) -> None:
        """Send password reset email"""
        try:
            subject, body = EmailTemplates.password_reset_email(reset_link)
            await NotificationService.send_email(
                to=email,
                subject=subject,
                body=body
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {e}")
            raise
    
    @staticmethod
    async def send_account_locked_notification(
        email: str,
        method: str = "email"
    ) -> None:
        """Send account locked notification"""
        try:
            if method == "email":
                subject, body = EmailTemplates.account_locked_email()
                await NotificationService.send_email(
                    to=email,
                    subject=subject,
                    body=body
                )
            elif method == "sms":
                await NotificationService.send_sms(
                    phone=email,
                    message="Your account has been locked due to failed login attempts."
                )
        except Exception as e:
            logger.error(f"Failed to send account locked notification: {e}")
    
    @staticmethod
    async def send_welcome_email(
        email: str,
        username: str
    ) -> None:
        """Send welcome email to new user"""
        try:
            subject, body = EmailTemplates.welcome_email(username)
            await NotificationService.send_email(
                to=email,
                subject=subject,
                body=body
            )
        except Exception as e:
            logger.error(f"Failed to send welcome email to {email}: {e}")
    
    @staticmethod
    async def send_email(
        to: str,
        subject: str,
        body: str,
        html: Optional[str] = None
    ) -> None:
        """Send email notification
        
        In production, integrate with SendGrid, AWS SES, or similar service.
        Currently logs the notification.
        """
        try:
            logger.info(f"Email notification: To={to}, Subject={subject}")
            logger.debug(f"Email body: {body}")
            
            # TODO: Integrate with email provider (SendGrid, AWS SES, etc.)
            # Example using SendGrid:
            # sg = SendGridAPIClient(settings.sendgrid_api_key)
            # message = Mail(
            #     from_email=settings.from_email,
            #     to_emails=to,
            #     subject=subject,
            #     plain_text_content=body,
            #     html_content=html
            # )
            # sg.send(message)
            
            # For now, just log
            return
        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            raise
    
    @staticmethod
    async def send_sms(
        phone: str,
        message: str
    ) -> None:
        """Send SMS notification
        
        In production, integrate with Twilio, AWS SNS, or similar service.
        Currently logs the notification.
        """
        try:
            logger.info(f"SMS notification: To={phone}, Message={message}")
            
            # TODO: Integrate with SMS provider (Twilio, AWS SNS, etc.)
            # Example using Twilio:
            # from twilio.rest import Client
            # client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            # message = client.messages.create(
            #     body=message,
            #     from_=settings.twilio_phone_number,
            #     to=phone
            # )
            
            # For now, just log
            return
        except Exception as e:
            logger.error(f"SMS notification failed: {e}")
            raise
    
    @staticmethod
    async def send_email(to: str, subject: str, body: str, data: Optional[Dict] = None) -> None:
        """Send email"""
        try:
            # In production, integrate with email service like SendGrid, AWS SES, etc.
            logger.info(f"Email sent: {to} - {subject} (mock implementation)")
            logger.debug(f"Email content - to: {to}, subject: {subject}, data: {data}")
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            raise
    
    @staticmethod
    async def send_sms(to: str, message: str) -> None:
        """Send SMS"""
        try:
            # In production, use Twilio, AWS SNS, etc.
            logger.info(f"SMS sent to {to} (mock implementation)")
            logger.debug(f"SMS content - to: {to}, message: {message}")
        except Exception as e:
            logger.error(f"SMS sending failed: {e}")
            raise
