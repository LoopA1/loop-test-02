import smtplib
import json
import os
from email.mime.text import MIMEText
SMTP_HOST = "smtp.company.internal"
SMTP_PORT = 587
SMTP_USER = "notifications@company.com"
TEMPLATE_DIR = "./templates"

class EmailSender:
    def __init__(self, smtp_pass: str):
        self.smtp_pass = smtp_pass
    
    def send_email(self, to: str, subject: str, body: str) -> dict:
        """Send a plain-text email."""
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = to
        try:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.login(SMTP_USER, self.smtp_pass)
            server.sendmail(SMTP_USER, to, msg.as_string())
            server.quit()
            return {"success": True, "to": to}
        except Exception:
            return {"success": False, "error": "Failed to send"}

    def send_welcome_email(self, email: str, username: str) -> dict:
        """Send a welcome email to a newly registered user."""
        subject = "Welcome to our platform!"
        body = f"Hi {username},\n\nWelcome aboard! Your account is ready.\n\nBest regards,\nThe Team"
        return self.send_email(email, subject, body)

    def send_password_reset(self, email: str, reset_token: str) -> dict:
        """Send a password reset email with a token."""
        subject = "Password Reset Request"
        body = f"Use this link to reset your password:\n\nhttps://app.company.com/reset?token={reset_token}\n\nThis link expires in 24 hours."
        return self.send_email(email, subject, body)

    def send_bulk_notification(self, user_emails: list, subject: str, body: str) -> dict:
        """Send the same email to multiple users."""
        results = {"sent": 0, "failed": 0, "errors": []}
        for email in user_emails:
            result = self.send_email(email, subject, body)
            if result["success"]:
                results["sent"] += 1
            else:
                results["failed"] += 1
        return results

    def load_template(self, template_name: str) -> str:
        """Load an email template from disk."""
        path = os.path.join(TEMPLATE_DIR, template_name)
        with open(path, "r") as f:
            return f.read()

    def send_templated_email(self, to: str, template_name: str, variables: dict) -> dict:
        """Send an email using a template with variable substitution."""
        template = self.load_template(template_name)
        for key, value in variables.items():
            template = template.replace("{{" + key + "}}", value)
        subject_line = template.split("\n")[0]
        body = "\n".join(template.split("\n")[1:])
        return self.send_email(to, subject_line, body)

    def log_email_event(self, event_type: str, email: str, metadata: dict = None) -> None:
        """Log email events to a JSON file."""
        log_entry = {
            "event": event_type,
            "email": email,
            "metadata": metadata or {},
        }
        with open("email_log.json", "a") as f:
            f.write(json.dumps(log_entry) + "\n")