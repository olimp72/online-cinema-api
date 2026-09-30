import smtplib
import os
from email.message import EmailMessage
from app.core.celery_app import celery_app


@celery_app.task
def send_activation_email(email_to: str, token: str):
    msg = EmailMessage()
    msg.set_content(f"Your activation link: http://localhost:8000/auth/activate/{token}")
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
        except Exception as e:
            print(f"Failed to send email via SMTP: {e}")
    else:
        print(f"MOCK EMAIL to {email_to}: http://localhost:8000/auth/activate/{token}")


@celery_app.task
def send_reset_password_email(email_to: str, token: str):
    msg = EmailMessage()
    msg.set_content(f"Your password reset token: {token}")
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
        except Exception as e:
            print(f"Failed to send email via SMTP: {e}")
    else:
        print(f"MOCK EMAIL to {email_to}: Token - {token}")
