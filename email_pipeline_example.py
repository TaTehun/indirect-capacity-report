"""
email_pipeline_example.py

Reference implementation of the email pipeline.
Copy and split into email_setup.py / sender.py for production use.

Sections:
  1. Configuration  (email_setup.py)
  2. Sender         (sender.py)
"""

# ============================================================
# 1. CONFIGURATION  (email_setup.py)
# ============================================================
from pathlib import Path

DESKTOP_PATH = Path.home() / 'Desktop'
_BASE        = DESKTOP_PATH / 'YOUR_PROJECT_FOLDER'

AIR_DIR      = _BASE / 'AIR inbound'   / 'final'
OCEAN_DIR    = _BASE / 'Ocean inbound' / 'final'
OTR_DIR      = _BASE / 'OTR inbound'   / 'final'
CAPACITY_DIR = _BASE / 'Capacity'

# .env file path, holds SMTP credentials
ENV_PATH = Path(r'C:\path\to\your\.env')

# SMTP
SMTP_SERVER   = 'smtp.your-mail-server.com'
SMTP_PORT     = 25
SMTP_USER_ENV = 'SMTP_USERNAME'    # key name in .env
SMTP_PASS_ENV = 'SMTP_PASSWORD'    # key name in .env

NOTIFICATION_FROM = 'your-sender@example.com'

ATTACHMENT_MIME = ("application", "vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Report email
EMAIL_SUBJECT = 'Inbound Capacity Report WK{}'    # .format(week_num)
EMAIL_TO      = ['recipient@example.com']
EMAIL_CC      = []
EMAIL_BCC     = []

# Failure alert email
EMAIL_SUBJECT_FAILURE = 'FAILED - Inbound Capacity Report WK{}'
EMAIL_TO_FAILURE      = ['admin@example.com']
EMAIL_CC_FAILURE      = []


# ============================================================
# 2. SENDER  (sender.py)
# ============================================================
import os
import smtplib
import logging

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.utils import formatdate
from email import encoders
from typing import List, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class EmailSender:
    """
    Low-level SMTP sender.
    """

    def __init__(self, user: str, password: str):
        self.user = user
        self.password = password

    def send(
        self,
        subject: str,
        body: str,
        to: List[str],
        cc: List[str] = None,
        bcc: List[str] = None,
        sender: str = None,
        attachment: Optional[Path] = None,
        attachment_mime: tuple = ATTACHMENT_MIME,
    ) -> bool:
        cc  = cc  or []
        bcc = bcc or []
        from_addr = sender or NOTIFICATION_FROM

        root = MIMEMultipart('related')
        root['From']    = from_addr
        root['To']      = ','.join(to)
        root['Cc']      = ','.join(cc)
        root['Date']    = formatdate(localtime=True)
        root['Subject'] = subject

        alt = MIMEMultipart('alternative')
        root.attach(alt)
        alt.attach(MIMEText(body, 'html', 'utf-8'))

        if attachment:
            attachment = Path(attachment)
            if attachment.exists():
                part = MIMEBase(*attachment_mime)
                part.set_payload(attachment.read_bytes())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename=attachment.name)
                root.attach(part)
            else:
                logger.warning(f"Attachment not found, skipping: {attachment}")

        recipients = to + cc + bcc
        try:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
                smtp.login(self.user, self.password)
                smtp.sendmail(from_addr, recipients, root.as_string())
            logger.info(f"Mail sent → {recipients}")
            return True
        except Exception as e:
            logger.error(f"Failed to send mail: {e}", exc_info=True)
            return False


def load_sender() -> Optional[EmailSender]:
    """Load SMTP credentials from .env and return an EmailSender instance."""
    load_dotenv(ENV_PATH)
    user = os.environ.get(SMTP_USER_ENV)
    pw   = os.environ.get(SMTP_PASS_ENV)
    if not user or not pw:
        logger.error("SMTP credentials missing")
        return None
    return EmailSender(user, pw)
