"""Servicio de mensajería WhatsApp vía Twilio."""

import logging

from twilio.rest import Client

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class WhatsAppService:
    def __init__(self):
        self._client = None
        if settings.twilio_account_sid and settings.twilio_auth_token:
            self._client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        self.from_number = settings.twilio_whatsapp_from

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def send_message(self, to: str, body: str) -> dict:
        if not self._client:
            logger.info("[WhatsApp SIMULADO] Para: %s | Mensaje: %s", to, body[:200])
            return {"sid": "simulated", "status": "simulated", "to": to}

        if not to.startswith("whatsapp:"):
            to = f"whatsapp:{to}"

        message = self._client.messages.create(body=body, from_=self.from_number, to=to)
        return {"sid": message.sid, "status": message.status, "to": to}

    def parse_incoming(self, form_data: dict) -> dict:
        """Parsea webhook de Twilio."""
        return {
            "from": form_data.get("From", "").replace("whatsapp:", ""),
            "to": form_data.get("To", ""),
            "body": form_data.get("Body", "").strip(),
            "message_sid": form_data.get("MessageSid", ""),
            "profile_name": form_data.get("ProfileName", ""),
        }
