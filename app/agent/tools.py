"""Herramientas del agente con acceso controlado al ATS."""

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.database import CandidateStatus, InterviewType
from app.services.ats_repository import ATSRepository
from app.services.calendar import CalendarService
from app.services.reports import ReportService
from app.services.star_interview import StarInterviewService

settings = get_settings()

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_candidato",
            "description": "Busca un candidato en el ATS por teléfono, WhatsApp o ID externo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "telefono": {"type": "string", "description": "Número de teléfono del candidato"},
                    "whatsapp_id": {"type": "string", "description": "ID de WhatsApp del candidato"},
                    "external_id": {"type": "string", "description": "ID externo del candidato (ej: CAND-9821)"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_vacantes",
            "description": "Lista las vacantes activas en el ATS.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "listar_candidatos",
            "description": "Lista candidatos filtrados por vacante o estado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "position_external_id": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": [s.value for s in CandidateStatus],
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_candidato",
            "description": "Registra un nuevo candidato. Solo si no existe previamente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string"},
                    "email": {"type": "string"},
                    "telefono": {"type": "string"},
                    "puesto_actual": {"type": "string"},
                    "empresa_actual": {"type": "string"},
                    "anos_experiencia": {"type": "integer"},
                    "expectativa_salarial": {"type": "number"},
                    "disponibilidad": {"type": "string"},
                    "position_external_id": {"type": "string"},
                },
                "required": ["nombre"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cambiar_estado_candidato",
            "description": "Cambia el estado de un candidato en el pipeline. Registra historial.",
            "parameters": {
                "type": "object",
                "properties": {
                    "external_id": {"type": "string"},
                    "nuevo_estado": {
                        "type": "string",
                        "enum": [s.value for s in CandidateStatus],
                    },
                    "motivo": {"type": "string"},
                },
                "required": ["external_id", "nuevo_estado"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "agregar_nota_candidato",
            "description": "Agrega una nota al candidato sin sobrescribir notas existentes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "external_id": {"type": "string"},
                    "nota": {"type": "string"},
                },
                "required": ["external_id", "nota"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_disponibilidad_entrevistador",
            "description": "Consulta huecos libres del entrevistador en su calendario corporativo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email_entrevistador": {"type": "string"},
                    "calendar_id": {"type": "string", "default": "primary"},
                },
                "required": ["email_entrevistador"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "agendar_entrevista_presencial",
            "description": "Agenda entrevista presencial: crea registro en ATS y evento en calendario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "external_id": {"type": "string"},
                    "fecha_hora": {"type": "string", "description": "ISO 8601, ej: 2026-06-10T10:00:00"},
                    "email_entrevistador": {"type": "string"},
                    "nombre_entrevistador": {"type": "string"},
                    "puesto_entrevistador": {"type": "string"},
                    "ubicacion": {"type": "string"},
                    "duracion_minutos": {"type": "integer", "default": 60},
                },
                "required": ["external_id", "fecha_hora", "email_entrevistador", "ubicacion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_evaluacion_star",
            "description": "Registra evaluación STAR de entrevista por competencias (máx 3 competencias).",
            "parameters": {
                "type": "object",
                "properties": {
                    "external_id": {"type": "string"},
                    "evaluaciones": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "competencia": {"type": "string"},
                                "pregunta": {"type": "string"},
                                "situacion": {"type": "string"},
                                "tarea": {"type": "string"},
                                "accion": {"type": "string"},
                                "resultado": {"type": "string"},
                                "calificacion": {"type": "integer", "minimum": 1, "maximum": 4},
                            },
                            "required": ["competencia", "calificacion"],
                        },
                        "maxItems": 3,
                    },
                    "conclusion": {"type": "string"},
                },
                "required": ["external_id", "evaluaciones"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generar_reporte_terna",
            "description": "Genera reporte ejecutivo de candidatos finalistas para el hiring manager.",
            "parameters": {
                "type": "object",
                "properties": {
                    "position_external_id": {"type": "string"},
                },
                "required": ["position_external_id"],
            },
        },
    },
]


class AgentTools:
    def __init__(self, db: Session):
        self.repo = ATSRepository(db)
        self.calendar = CalendarService()
        self.reports = ReportService()
        self.star = StarInterviewService()

    def execute(self, tool_name: str, arguments: dict[str, Any], context: dict[str, Any]) -> str:
        try:
            result = getattr(self, f"_tool_{tool_name}")(arguments, context)
            return json.dumps(result, ensure_ascii=False, default=str)
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": f"Error ejecutando {tool_name}: {e}"}, ensure_ascii=False)

    def _resolve_candidate(self, args: dict) -> Any:
        if args.get("external_id"):
            c = self.repo.get_candidate_by_external_id(args["external_id"])
            if c:
                return c
        if args.get("whatsapp_id"):
            c = self.repo.get_candidate_by_whatsapp(args["whatsapp_id"])
            if c:
                return c
        if args.get("telefono"):
            return self.repo.get_candidate_by_phone(args["telefono"])
        return None

    def _candidate_to_dict(self, c) -> dict:
        return {
            "external_id": c.external_id,
            "nombre": c.nombre,
            "email": c.email,
            "telefono": c.telefono,
            "puesto_actual": c.puesto_actual,
            "empresa_actual": c.empresa_actual,
            "anos_experiencia": c.anos_experiencia,
            "expectativa_salarial": c.expectativa_salarial,
            "moneda_salarial": c.moneda_salarial,
            "disponibilidad": c.disponibilidad,
            "status": c.status.value,
            "fortalezas": c.fortalezas,
            "areas_oportunidad": c.areas_oportunidad,
            "notas_reclutador": c.notas_reclutador,
            "vacante": c.position.title if c.position else None,
        }

    def _tool_buscar_candidato(self, args: dict, ctx: dict) -> dict:
        c = self._resolve_candidate(args)
        if not c:
            return {"encontrado": False, "mensaje": "No se encontró candidato con esos criterios en el ATS."}
        return {"encontrado": True, "candidato": self._candidate_to_dict(c)}

    def _tool_listar_vacantes(self, args: dict, ctx: dict) -> dict:
        positions = self.repo.list_positions()
        return {
            "vacantes": [
                {
                    "external_id": p.external_id,
                    "title": p.title,
                    "department": p.department,
                    "hiring_manager": p.hiring_manager_name,
                    "location": p.location,
                    "competencias_clave": p.key_competencies,
                }
                for p in positions
            ]
        }

    def _tool_listar_candidatos(self, args: dict, ctx: dict) -> dict:
        position_id = None
        if args.get("position_external_id"):
            pos = self.repo.get_position_by_external_id(args["position_external_id"])
            if not pos:
                return {"error": f"Vacante {args['position_external_id']} no encontrada."}
            position_id = pos.id

        status = CandidateStatus(args["status"]) if args.get("status") else None
        candidates = self.repo.list_candidates(position_id=position_id, status=status)
        return {"total": len(candidates), "candidatos": [self._candidate_to_dict(c) for c in candidates]}

    def _tool_registrar_candidato(self, args: dict, ctx: dict) -> dict:
        data = dict(args)
        if args.get("position_external_id"):
            pos = self.repo.get_position_by_external_id(args["position_external_id"])
            if not pos:
                return {"error": f"Vacante {args['position_external_id']} no encontrada."}
            data["position_id"] = pos.id
        data["whatsapp_id"] = ctx.get("whatsapp_id")
        if not data.get("telefono") and ctx.get("whatsapp_id"):
            data["telefono"] = ctx["whatsapp_id"]

        candidate = self.repo.create_candidate(data)
        return {"creado": True, "candidato": self._candidate_to_dict(candidate)}

    def _tool_cambiar_estado_candidato(self, args: dict, ctx: dict) -> dict:
        c = self.repo.get_candidate_by_external_id(args["external_id"])
        if not c:
            return {"error": f"Candidato {args['external_id']} no encontrado."}
        new_status = CandidateStatus(args["nuevo_estado"])
        updated = self.repo.update_candidate_status(
            c, new_status, settings.default_recruiter_name, args.get("motivo")
        )
        return {"actualizado": True, "nuevo_estado": updated.status.value}

    def _tool_agregar_nota_candidato(self, args: dict, ctx: dict) -> dict:
        c = self.repo.get_candidate_by_external_id(args["external_id"])
        if not c:
            return {"error": f"Candidato {args['external_id']} no encontrado."}
        self.repo.append_candidate_note(c, args["nota"])
        return {"nota_agregada": True}

    def _tool_consultar_disponibilidad_entrevistador(self, args: dict, ctx: dict) -> dict:
        slots = self.calendar.get_available_slots(
            args["email_entrevistador"],
            args.get("calendar_id", "primary"),
        )
        return {"disponibilidad": slots}

    def _tool_agendar_entrevista_presencial(self, args: dict, ctx: dict) -> dict:
        c = self.repo.get_candidate_by_external_id(args["external_id"])
        if not c:
            return {"error": f"Candidato {args['external_id']} no encontrado."}
        if not c.email:
            return {"error": "El candidato no tiene email registrado. Solicítalo antes de agendar."}

        from datetime import timedelta

        fecha_hora = datetime.fromisoformat(args["fecha_hora"])
        duracion = args.get("duracion_minutos", 60)
        ubicacion = args["ubicacion"]
        vacante = c.position.title if c.position else "Entrevista"
        event_end = fecha_hora + timedelta(minutes=duracion)

        event = self.calendar.create_event(
            calendar_id="primary",
            summary=f"Entrevista Presencial: {vacante} – {c.nombre}",
            start=fecha_hora,
            end=event_end,
            location=ubicacion,
            attendees=[args["email_entrevistador"], c.email],
            description=f"Entrevista presencial para {vacante}",
        )

        interview = self.repo.schedule_interview(
            candidate=c,
            entrevistador_email=args["email_entrevistador"],
            entrevistador_nombre=args.get("nombre_entrevistador", "Entrevistador"),
            entrevistador_puesto=args.get("puesto_entrevistador", ""),
            tipo=InterviewType.PRESENCIAL,
            fecha_hora=fecha_hora,
            ubicacion=ubicacion,
            duracion_minutos=duracion,
            calendar_event_id=event.get("event_id"),
        )

        self.repo.update_candidate_status(
            c,
            CandidateStatus.ENTREVISTA_PRESENCIAL,
            settings.default_recruiter_name,
            "Entrevista presencial agendada",
        )

        return {
            "agendado": True,
            "interview_id": interview.id,
            "fecha_hora": fecha_hora.isoformat(),
            "ubicacion": ubicacion,
            "calendar_event_id": event.get("event_id"),
        }

    def _tool_registrar_evaluacion_star(self, args: dict, ctx: dict) -> dict:
        c = self.repo.get_candidate_by_external_id(args["external_id"])
        if not c:
            return {"error": f"Candidato {args['external_id']} no encontrado."}

        evaluaciones = args.get("evaluaciones", [])
        if len(evaluaciones) > 3:
            return {"error": "Máximo 3 competencias por entrevista STAR."}

        for ev in evaluaciones:
            errors = self.star.validate_evaluation(ev)
            if errors:
                return {"error": "; ".join(errors)}

        interview = self.repo.create_star_interview(
            c,
            settings.default_recruiter_name,
            evaluaciones,
            args.get("conclusion"),
        )
        ficha = self.star.render_ficha(interview, c.nombre)
        return {"registrado": True, "ficha": ficha}

    def _tool_generar_reporte_terna(self, args: dict, ctx: dict) -> dict:
        pos = self.repo.get_position_by_external_id(args["position_external_id"])
        if not pos:
            return {"error": f"Vacante {args['position_external_id']} no encontrada."}

        finalists = self.repo.get_finalists(pos.id)
        report = self.reports.render_executive_report(pos, finalists)
        return {"reporte": report, "total_finalistas": len(finalists)}
