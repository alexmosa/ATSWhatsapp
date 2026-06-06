"""Orquestador del agente de reclutamiento conversacional."""

import json
import logging
from typing import Any

from openai import OpenAI
from sqlalchemy.orm import Session

from app.agent.persona import build_system_prompt
from app.agent.tools import TOOL_DEFINITIONS, AgentTools
from app.config import get_settings
from app.services.ats_repository import ATSRepository

logger = logging.getLogger(__name__)
settings = get_settings()
MAX_TOOL_ITERATIONS = 5


class RecruitmentAgent:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ATSRepository(db)
        self.tools = AgentTools(db)
        self.client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def process_message(self, whatsapp_id: str, message: str, profile_name: str = "") -> str:
        self.repo.log_conversation(whatsapp_id, "user", message)

        if not self.client:
            response = self._fallback_response(whatsapp_id, message)
            self.repo.log_conversation(whatsapp_id, "assistant", response)
            return response

        context = self._build_context(whatsapp_id, profile_name)
        messages = self._build_messages(context, whatsapp_id, message)
        response = self._run_agent_loop(messages, {"whatsapp_id": whatsapp_id})

        self.repo.log_conversation(whatsapp_id, "assistant", response)
        return response

    def _build_context(self, whatsapp_id: str, profile_name: str) -> str:
        parts = []
        candidate = self.repo.get_candidate_by_whatsapp(whatsapp_id)
        if not candidate:
            candidate = self.repo.get_candidate_by_phone(whatsapp_id)

        if candidate:
            parts.append(
                f"Candidato identificado en ATS: {candidate.nombre} "
                f"(ID: {candidate.external_id}, Estado: {candidate.status.value})"
            )
            if candidate.position:
                parts.append(f"Vacante asignada: {candidate.position.title}")
        elif profile_name:
            parts.append(f"Contacto WhatsApp: {profile_name} (no registrado aún en ATS)")

        positions = self.repo.list_positions()
        if positions:
            vacantes = ", ".join(f"{p.external_id}: {p.title}" for p in positions[:5])
            parts.append(f"Vacantes activas: {vacantes}")

        return "\n".join(parts) if parts else "Sin contexto previo en ATS."

    def _build_messages(self, context: str, whatsapp_id: str, message: str) -> list[dict]:
        system = build_system_prompt(settings.default_company_name, settings.default_recruiter_name)
        system += f"\n\n## Contexto actual del ATS\n{context}"

        history = self.repo.get_conversation_history(whatsapp_id, limit=10)
        messages = [{"role": "system", "content": system}]

        for log in reversed(history[1:]):
            role = "user" if log.role == "user" else "assistant"
            messages.append({"role": role, "content": log.content})

        messages.append({"role": "user", "content": message})
        return messages

    def _run_agent_loop(self, messages: list[dict], context: dict[str, Any]) -> str:
        for _ in range(MAX_TOOL_ITERATIONS):
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=0.4,
            )
            choice = response.choices[0]

            if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
                messages.append(choice.message)
                for tool_call in choice.message.tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments)
                    result = self.tools.execute(fn_name, fn_args, context)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        }
                    )
                continue

            return choice.message.content or "¿En qué más puedo ayudarte con el proceso de selección?"

        return "He procesado tu solicitud. ¿Hay algo más en lo que pueda asistirte?"

    def _fallback_response(self, whatsapp_id: str, message: str) -> str:
        """Respuestas básicas cuando OpenAI no está configurado."""
        lower = message.lower().strip()
        candidate = self.repo.get_candidate_by_whatsapp(whatsapp_id) or self.repo.get_candidate_by_phone(
            whatsapp_id
        )

        if any(w in lower for w in ["hola", "buenos", "buenas", "hey"]):
            name = candidate.nombre if candidate else ""
            greeting = f" {name}" if name else ""
            return (
                f"¡Hola{greeting}! Soy del equipo de Atracción de Talento. "
                "¿En qué puedo apoyarte hoy con tu proceso de selección?"
            )

        if any(w in lower for w in ["vacante", "vacantes", "puesto", "posición"]):
            positions = self.repo.list_positions()
            if not positions:
                return "Actualmente no hay vacantes activas registradas en nuestro sistema."
            lines = ["Estas son nuestras vacantes activas:\n"]
            for p in positions:
                lines.append(f"• {p.title} ({p.external_id})")
            return "\n".join(lines)

        if candidate:
            return (
                f"Hola {candidate.nombre}, tu proceso está en estado: {candidate.status.value}. "
                "¿Tienes alguna pregunta sobre los siguientes pasos?"
            )

        return (
            "Gracias por contactarnos. Para brindarte información precisa sobre tu proceso, "
            "¿podrías indicarme tu nombre completo y la vacante a la que aplicaste?"
        )
