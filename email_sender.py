import smtplib
import json
import os
from email.mime.text import MIMEText
from user_validator import UserValidator
import re
import logging

SMTP_HOST = "smtp.company.internal"
SMTP_PORT = 587
SMTP_USER = "notifications@company.com"
TEMPLATE_DIR = "./templates"

logger = logging.getLogger(__name__)

class EmailSender:
    def __init__(self, smtp_pass: str):
        self.smtp_pass = smtp_pass
        self.validator = UserValidator()

    def send_email(self, to: str, subject: str, body: str) -> dict:
        validation_result = self.validator.validate_email(to)
        if not validation_result['valid']:
            return {'error': 'Invalid email address', 'details': validation_result}
        if not to or len(to.strip()) == 0:
            return {'error': 'Email is required'}
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SMTP_USER
        msg['To'] = to
        try:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, self.smtp_pass)
            server.sendmail(SMTP_USER, to, msg.as_string())
            server.quit()
            return {'success': True, 'to': to}
        except Exception as e:
            logger.error(f'Failed to send email: {e}')
            return {'success': False, 'error': 'Failed to send'}