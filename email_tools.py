# -*- coding: utf-8 -*-
"""
Gmail integration for פוני - sends emails via SMTP.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger("פוני-email")


def send_email(to: str, subject: str, body: str) -> str:
    """Send an email via Gmail SMTP."""
    gmail_user = os.getenv("GMAIL_USER", "")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "")

    if not gmail_user or not gmail_app_password:
        return "שגיאה: פרטי Gmail לא מוגדרים."

    try:
        msg = MIMEMultipart()
        msg["From"] = gmail_user
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_app_password)
            server.sendmail(gmail_user, to, msg.as_string())

        logger.info(f"Email sent to {to}: {subject}")
        return f"המייל נשלח בהצלחה אל {to}."
    except Exception as e:
        logger.error(f"Email error: {e}")
        return f"שגיאה בשליחת המייל: {e}"
