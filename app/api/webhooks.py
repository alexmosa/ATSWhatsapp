"""Webhooks de WhatsApp (Twilio)."""

import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.agent.orchestrator import RecruitmentAgent
from app.models.database import get_db
from app.services.whatsapp import WhatsAppService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])
whatsapp = WhatsAppService()


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Recibe mensajes entrantes de WhatsApp vía Twilio.
    Configura en Twilio: POST {WEBHOOK_BASE_URL}/webhooks/whatsapp
    """
    form = await request.form()
    incoming = whatsapp.parse_incoming(dict(form))

    if not incoming["body"]:
        return Response(content="<Response></Response>", media_type="application/xml")

    logger.info("WhatsApp de %s: %s", incoming["from"], incoming["body"][:100])

    agent = RecruitmentAgent(db)
    reply = agent.process_message(
        whatsapp_id=incoming["from"],
        message=incoming["body"],
        profile_name=incoming.get("profile_name", ""),
    )

    whatsapp.send_message(to=incoming["from"], body=reply)

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{_escape_xml(reply[:1500])}</Message>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@router.post("/whatsapp/status")
async def whatsapp_status(request: Request):
    """Webhook de estado de mensajes Twilio (entregado, leído, etc.)."""
    form = await request.form()
    logger.info("Estado mensaje %s: %s", form.get("MessageSid"), form.get("MessageStatus"))
    return {"status": "ok"}


def _escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
