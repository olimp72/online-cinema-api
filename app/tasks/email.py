import smtplib
import os
import logging
from email.message import EmailMessage
from app.core.celery_app import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_activation_email(self, email_to: str, token: str):
    activation_url = f"{settings.FRONTEND_URL}/auth/activate/{token}"
    msg = EmailMessage()
    msg.set_content(f"Your activation link: {activation_url}")
    msg["Subject"] = "Account Activation"
    msg["From"] = os.getenv("SMTP_USER", "noreply@online-cinema.local")
    msg["To"] = email_to

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    if smtp_host and smtp_port:
        try:
            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            logger.info(f"Activation email successfully sent to {email_to}")
        except Exception as e:
            logger.error(f"Failed to send activation email to {email_to}: {e}")
            raise self.retry(exc=e)
    else:
        logger.info(f"MOCK EMAIL to {email_to}: {activation_url}")


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_reset_password_email(self, email_to: str, token: str):
    reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={token}"
    msg = EmailMessage()
    msg.set_content(f"Your password reset link: {reset_url}")
    msg["Subject"] = "Password Reset"
    msg["From"] = os.getenv("SMTP_USER", "noreply@online-cinema.local")
    msg["To"] = email_to

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    if smtp_host and smtp_port:
        try:
            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            logger.info(f"Password reset email successfully sent to {email_to}")
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email_to}: {e}")
            raise self.retry(exc=e)
    else:
        logger.info(f"MOCK EMAIL to {email_to}: {reset_url}")
