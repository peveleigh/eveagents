"""Emailer Class."""
from __future__ import annotations

import logging
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class SMTPConfigError(ValueError):
    """Raised when required SMTP environment variables are missing or invalid."""

    def __init__(self, missing: list[str]) -> None:
        """Initialize with the list of missing variable names."""
        self.missing = missing
        super().__init__(
            "Required SMTP environment variables not set: " + ", ".join(missing),
        )


class Emailer:
    """SMTP Email Class."""

    def __init__(self) -> None:
        """Initialize and validate SMTP configuration from the environment."""
        self.smtp_host = os.environ.get("SMTP_HOST")
        port_raw = os.environ.get("SMTP_PORT", "587")
        self.smtp_user = os.environ.get("SMTP_USER")
        self.smtp_password = os.environ.get("SMTP_PASSWORD")
        self.sender_email = os.environ.get("SENDER_EMAIL")
        self.recipient_email = os.environ.get("RECIPIENT_EMAIL")

        missing: list[str] = []
        if not self.smtp_host:
            missing.append("SMTP_HOST")
        if not self.smtp_user:
            missing.append("SMTP_USER")
        if not self.smtp_password:
            missing.append("SMTP_PASSWORD")
        if not self.sender_email:
            missing.append("SENDER_EMAIL")
        if not self.recipient_email:
            missing.append("RECIPIENT_EMAIL")

        try:
            self.smtp_port = int(port_raw)
        except (TypeError, ValueError) as exc:
            raise SMTPConfigError(["SMTP_PORT"]) from exc

        if missing:
            raise SMTPConfigError(missing)

    def send_email(
        self,
        subject: str,
        body: str,
        attachment_path: str | None = None,
    ) -> bool:
        """Send an email with optional attachment.

        Args:
            recipient_email: Email address of the recipient
            subject: Subject line of the email
            body: Plain text body of the email
            attachment_path: Optional path to a file to attach

        Returns:
            bool: True if email was sent successfully, False otherwise

        """
        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = self.recipient_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        if attachment_path:
            try:
                with Path(attachment_path).open("rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f'attachment; filename="{Path(attachment_path).name}"',
                )
                msg.attach(part)
            except FileNotFoundError:
                logger.exception("Attachment file not found: %s", attachment_path)
                return False

        server = None
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, self.recipient_email, text)
            logger.info("Email sent successfully!")
        except Exception:
            logger.exception("Failed to send email:")
            return False
        else:
            return True
        finally:
            if server is not None:
                server.quit()

