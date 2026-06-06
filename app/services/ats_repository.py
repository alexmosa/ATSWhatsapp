"""Repositorio ATS con operaciones seguras: sin borrado ni sobrescritura destructiva."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.database import (
    Candidate,
    CandidateStatus,
    CandidateStatusHistory,
    CompetencyEvaluation,
    ConversationLog,
    Interview,
    InterviewType,
    JobPosition,
    StarInterview,
)


class ATSRepository:
    """Capa de acceso a datos con políticas de no-borrado y no-sobrescritura."""

    def __init__(self, db: Session):
        self.db = db

    # ── Lecturas ──────────────────────────────────────────────────────────

    def get_candidate_by_external_id(self, external_id: str) -> Candidate | None:
        return self.db.query(Candidate).filter(Candidate.external_id == external_id).first()

    def get_candidate_by_whatsapp(self, whatsapp_id: str) -> Candidate | None:
        return self.db.query(Candidate).filter(Candidate.whatsapp_id == whatsapp_id).first()

    def get_candidate_by_phone(self, telefono: str) -> Candidate | None:
        return self.db.query(Candidate).filter(Candidate.telefono == telefono).first()

    def list_candidates(
        self,
        position_id: int | None = None,
        status: CandidateStatus | None = None,
        limit: int = 50,
    ) -> list[Candidate]:
        query = self.db.query(Candidate).filter(Candidate.is_active.is_(True))
        if position_id:
            query = query.filter(Candidate.position_id == position_id)
        if status:
            query = query.filter(Candidate.status == status)
        return query.order_by(Candidate.updated_at.desc()).limit(limit).all()

    def get_position_by_external_id(self, external_id: str) -> JobPosition | None:
        return self.db.query(JobPosition).filter(JobPosition.external_id == external_id).first()

    def list_positions(self, active_only: bool = True) -> list[JobPosition]:
        query = self.db.query(JobPosition)
        if active_only:
            query = query.filter(JobPosition.is_active.is_(True))
        return query.order_by(JobPosition.title).all()

    def get_finalists(self, position_id: int) -> list[Candidate]:
        return (
            self.db.query(Candidate)
            .filter(
                Candidate.position_id == position_id,
                Candidate.status == CandidateStatus.FINALISTA,
                Candidate.is_active.is_(True),
            )
            .all()
        )

    def get_conversation_history(self, whatsapp_id: str, limit: int = 20) -> list[ConversationLog]:
        return (
            self.db.query(ConversationLog)
            .filter(ConversationLog.whatsapp_id == whatsapp_id)
            .order_by(ConversationLog.created_at.desc())
            .limit(limit)
            .all()
        )

    # ── Escrituras seguras ──────────────────────────────────────────────────

    def create_candidate(self, data: dict[str, Any]) -> Candidate:
        external_id = data.get("external_id") or f"CAND-{uuid.uuid4().hex[:8].upper()}"
        existing = self.get_candidate_by_external_id(external_id)
        if existing:
            raise ValueError(f"El candidato {external_id} ya existe. No se permite sobrescribir.")

        candidate = Candidate(
            external_id=external_id,
            nombre=data["nombre"],
            email=data.get("email"),
            telefono=data.get("telefono"),
            whatsapp_id=data.get("whatsapp_id"),
            puesto_actual=data.get("puesto_actual"),
            empresa_actual=data.get("empresa_actual"),
            anos_experiencia=data.get("anos_experiencia"),
            expectativa_salarial=data.get("expectativa_salarial"),
            moneda_salarial=data.get("moneda_salarial", "MXN"),
            salario_tipo=data.get("salario_tipo", "brutos"),
            disponibilidad=data.get("disponibilidad"),
            nivel_ingles=data.get("nivel_ingles"),
            fortalezas=data.get("fortalezas", []),
            areas_oportunidad=data.get("areas_oportunidad", []),
            position_id=data.get("position_id"),
        )
        self.db.add(candidate)
        self.db.flush()

        self._record_status_change(candidate.id, None, CandidateStatus.NUEVO.value, "sistema", "Alta inicial")
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def create_position(self, data: dict[str, Any]) -> JobPosition:
        external_id = data.get("external_id") or f"POS-{uuid.uuid4().hex[:8].upper()}"
        existing = self.get_position_by_external_id(external_id)
        if existing:
            raise ValueError(f"La posición {external_id} ya existe. No se permite sobrescribir.")

        position = JobPosition(
            external_id=external_id,
            title=data["title"],
            department=data.get("department"),
            description=data.get("description"),
            key_competencies=data.get("key_competencies", []),
            salary_range_min=data.get("salary_range_min"),
            salary_range_max=data.get("salary_range_max"),
            currency=data.get("currency", "MXN"),
            hiring_manager_name=data.get("hiring_manager_name"),
            hiring_manager_email=data.get("hiring_manager_email"),
            location=data.get("location"),
        )
        self.db.add(position)
        self.db.commit()
        self.db.refresh(position)
        return position

    def update_candidate_status(
        self,
        candidate: Candidate,
        new_status: CandidateStatus,
        changed_by: str,
        reason: str | None = None,
    ) -> Candidate:
        if candidate.status == new_status:
            return candidate

        self._record_status_change(
            candidate.id,
            candidate.status.value,
            new_status.value,
            changed_by,
            reason,
        )
        candidate.status = new_status
        candidate.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def append_candidate_note(self, candidate: Candidate, note: str) -> Candidate:
        """Agrega nota sin sobrescribir las existentes."""
        timestamp = datetime.utcnow().strftime("%d/%m/%Y %H:%M")
        new_note = f"[{timestamp}] {note}"
        if candidate.notas_reclutador:
            candidate.notas_reclutador = f"{candidate.notas_reclutador}\n{new_note}"
        else:
            candidate.notas_reclutador = new_note
        candidate.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def append_fortaleza(self, candidate: Candidate, fortaleza: str) -> Candidate:
        fortalezas = list(candidate.fortalezas or [])
        if fortaleza not in fortalezas:
            fortalezas.append(fortaleza)
            candidate.fortalezas = fortalezas
            candidate.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(candidate)
        return candidate

    def append_area_oportunidad(self, candidate: Candidate, area: str) -> Candidate:
        areas = list(candidate.areas_oportunidad or [])
        if area not in areas:
            areas.append(area)
            candidate.areas_oportunidad = areas
            candidate.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(candidate)
        return candidate

    def fill_empty_candidate_field(
        self, candidate: Candidate, field: str, value: Any
    ) -> Candidate:
        """Solo actualiza campos vacíos; nunca sobrescribe valores existentes."""
        current = getattr(candidate, field, None)
        if current is not None and current != "" and current != []:
            raise ValueError(
                f"El campo '{field}' ya tiene valor ({current!r}). "
                "No se permite sobrescribir. Usa append_candidate_note para agregar contexto."
            )
        setattr(candidate, field, value)
        candidate.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def create_star_interview(
        self,
        candidate: Candidate,
        entrevistador: str,
        evaluaciones: list[dict[str, Any]],
        conclusion: str | None = None,
    ) -> StarInterview:
        position_title = candidate.position.title if candidate.position else None
        interview = StarInterview(
            candidate_id=candidate.id,
            position_title=position_title,
            entrevistador=entrevistador,
            conclusion_reclutador=conclusion,
        )
        self.db.add(interview)
        self.db.flush()

        for ev in evaluaciones:
            evaluation = CompetencyEvaluation(
                star_interview_id=interview.id,
                competencia=ev["competencia"],
                pregunta=ev.get("pregunta"),
                situacion=ev.get("situacion"),
                tarea=ev.get("tarea"),
                accion=ev.get("accion"),
                resultado=ev.get("resultado"),
                calificacion=ev.get("calificacion"),
                notas=ev.get("notas"),
            )
            self.db.add(evaluation)

        self.db.commit()
        self.db.refresh(interview)
        return interview

    def schedule_interview(
        self,
        candidate: Candidate,
        entrevistador_email: str,
        entrevistador_nombre: str,
        entrevistador_puesto: str,
        tipo: InterviewType,
        fecha_hora: datetime,
        ubicacion: str | None = None,
        duracion_minutos: int = 60,
        calendar_event_id: str | None = None,
    ) -> Interview:
        interview = Interview(
            candidate_id=candidate.id,
            entrevistador_email=entrevistador_email,
            entrevistador_nombre=entrevistador_nombre,
            entrevistador_puesto=entrevistador_puesto,
            tipo=tipo,
            fecha_hora=fecha_hora,
            ubicacion=ubicacion,
            duracion_minutos=duracion_minutos,
            calendar_event_id=calendar_event_id,
        )
        self.db.add(interview)
        self.db.commit()
        self.db.refresh(interview)
        return interview

    def log_conversation(self, whatsapp_id: str, role: str, content: str) -> ConversationLog:
        log = ConversationLog(whatsapp_id=whatsapp_id, role=role, content=content)
        self.db.add(log)
        self.db.commit()
        return log

    def _record_status_change(
        self,
        candidate_id: int,
        previous: str | None,
        new: str,
        changed_by: str,
        reason: str | None,
    ) -> None:
        history = CandidateStatusHistory(
            candidate_id=candidate_id,
            previous_status=previous,
            new_status=new,
            changed_by=changed_by,
            reason=reason,
        )
        self.db.add(history)
