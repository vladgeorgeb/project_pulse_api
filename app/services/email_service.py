from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage as SMTPMessage
from email.utils import formataddr
from typing import Protocol

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class OutboundEmail:
    to_email: str
    subject: str
    text_body: str


class EmailBackend(Protocol):
    def send(self, message: OutboundEmail) -> None: ...


local_email_outbox: list[OutboundEmail] = []


class ConsoleEmailBackend:
    def send(self, message: OutboundEmail) -> None:
        local_email_outbox.append(message)
        logger.info(
            "Stored local email for %s with subject %s.",
            message.to_email,
            message.subject,
        )


class SMTPEmailBackend:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send(self, message: OutboundEmail) -> None:
        smtp_message = SMTPMessage()
        smtp_message["From"] = formataddr(
            (self.settings.email_from_name, self.settings.email_from_email)
        )
        smtp_message["To"] = message.to_email
        smtp_message["Subject"] = message.subject
        smtp_message.set_content(message.text_body)

        if self.settings.smtp_host is None:
            raise RuntimeError("SMTP_HOST is required when EMAIL_BACKEND=smtp.")

        if self.settings.smtp_use_ssl:
            with smtplib.SMTP_SSL(
                self.settings.smtp_host,
                self.settings.smtp_port,
            ) as client:
                self._send_with_client(client, smtp_message)
            return

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as client:
            if self.settings.smtp_use_tls:
                client.starttls()
            self._send_with_client(client, smtp_message)

    def _send_with_client(
        self,
        client: smtplib.SMTP | smtplib.SMTP_SSL,
        message: SMTPMessage,
    ) -> None:
        if self.settings.smtp_username and self.settings.smtp_password:
            client.login(self.settings.smtp_username, self.settings.smtp_password)
        client.send_message(message)


class EmailService:
    def __init__(
        self,
        settings: Settings | None = None,
        backend: EmailBackend | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.backend = backend or self._backend_for_settings(self.settings)

    def send_password_reset_email(self, *, to_email: str, token: str) -> None:
        reset_url = f"{self.settings.frontend_base_url}/reset-password?token={token}"
        self.backend.send(
            OutboundEmail(
                to_email=to_email,
                subject="Reset your Project Pulse password",
                text_body=(
                    "Use this link to reset your Project Pulse password:\n\n"
                    f"{reset_url}\n\n"
                    "If you did not request this, you can ignore this email."
                ),
            )
        )

    def send_email_confirmation_email(self, *, to_email: str, token: str) -> None:
        confirmation_url = (
            f"{self.settings.frontend_base_url}/confirm-email?token={token}"
        )
        self.backend.send(
            OutboundEmail(
                to_email=to_email,
                subject="Confirm your Project Pulse email",
                text_body=(
                    "Confirm your Project Pulse email address with this link:\n\n"
                    f"{confirmation_url}\n\n"
                    "If you did not create this account, you can ignore this email."
                ),
            )
        )

    def _backend_for_settings(self, settings: Settings) -> EmailBackend:
        if settings.email_backend == "smtp":
            return SMTPEmailBackend(settings)
        return ConsoleEmailBackend()
