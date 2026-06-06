"""API REST del ATS para integraciones externas."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.database import CandidateStatus, get_db
from app.services.ats_repository import ATSRepository
from app.services.reports import ReportService
from app.services.star_interview import StarInterviewService

router = APIRouter(prefix="/api/ats", tags=["ats"])


class PositionCreate(BaseModel):
    title: str
    department: str | None = None
    description: str | None = None
    key_competencies: list[str] = Field(default_factory=list)
    salary_range_min: float | None = None
    salary_range_max: float | None = None
    currency: str = "MXN"
    hiring_manager_name: str | None = None
    hiring_manager_email: str | None = None
    location: str | None = None
    external_id: str | None = None


class CandidateCreate(BaseModel):
    nombre: str
    email: str | None = None
    telefono: str | None = None
    whatsapp_id: str | None = None
    puesto_actual: str | None = None
    empresa_actual: str | None = None
    anos_experiencia: int | None = None
    expectativa_salarial: float | None = None
    disponibilidad: str | None = None
    position_external_id: str | None = None


class StatusChange(BaseModel):
    nuevo_estado: CandidateStatus
    motivo: str | None = None
    changed_by: str = "api"


class StarEvaluationItem(BaseModel):
    competencia: str
    pregunta: str | None = None
    situacion: str | None = None
    tarea: str | None = None
    accion: str | None = None
    resultado: str | None = None
    calificacion: int = Field(ge=1, le=4)


class StarEvaluationCreate(BaseModel):
    evaluaciones: list[StarEvaluationItem] = Field(max_length=3)
    conclusion: str | None = None
    entrevistador: str = "Reclutador Senior"


class ScheduleInterviewPayload(BaseModel):
    """Payload del webhook ATS → motor de integración → calendario."""
    candidato: dict[str, str]
    entrevistador: dict[str, str]
    detalles_evento: dict[str, Any]


@router.get("/health")
def health():
    return {"status": "ok", "service": "ATS WhatsApp"}


@router.get("/positions")
def list_positions(db: Session = Depends(get_db)):
    repo = ATSRepository(db)
    positions = repo.list_positions()
    return [
        {
            "external_id": p.external_id,
            "title": p.title,
            "department": p.department,
            "hiring_manager": p.hiring_manager_name,
            "location": p.location,
            "competencies": p.key_competencies,
        }
        for p in positions
    ]


@router.post("/positions", status_code=201)
def create_position(payload: PositionCreate, db: Session = Depends(get_db)):
    repo = ATSRepository(db)
    try:
        position = repo.create_position(payload.model_dump())
        return {"external_id": position.external_id, "title": position.title}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/candidates")
def list_candidates(
    status: CandidateStatus | None = None,
    position_id: str | None = None,
    db: Session = Depends(get_db),
):
    repo = ATSRepository(db)
    pos_id = None
    if position_id:
        pos = repo.get_position_by_external_id(position_id)
        if not pos:
            raise HTTPException(status_code=404, detail="Vacante no encontrada")
        pos_id = pos.id

    candidates = repo.list_candidates(position_id=pos_id, status=status)
    return [
        {
            "external_id": c.external_id,
            "nombre": c.nombre,
            "email": c.email,
            "telefono": c.telefono,
            "status": c.status.value,
            "vacante": c.position.title if c.position else None,
        }
        for c in candidates
    ]


@router.post("/candidates", status_code=201)
def create_candidate(payload: CandidateCreate, db: Session = Depends(get_db)):
    repo = ATSRepository(db)
    data = payload.model_dump()
    if payload.position_external_id:
        pos = repo.get_position_by_external_id(payload.position_external_id)
        if not pos:
            raise HTTPException(status_code=404, detail="Vacante no encontrada")
        data["position_id"] = pos.id

    try:
        candidate = repo.create_candidate(data)
        return {"external_id": candidate.external_id, "nombre": candidate.nombre}
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/candidates/{external_id}")
def get_candidate(external_id: str, db: Session = Depends(get_db)):
    repo = ATSRepository(db)
    c = repo.get_candidate_by_external_id(external_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidato no encontrado")
    return {
        "external_id": c.external_id,
        "nombre": c.nombre,
        "email": c.email,
        "telefono": c.telefono,
        "status": c.status.value,
        "puesto_actual": c.puesto_actual,
        "empresa_actual": c.empresa_actual,
        "expectativa_salarial": c.expectativa_salarial,
        "fortalezas": c.fortalezas,
        "areas_oportunidad": c.areas_oportunidad,
        "notas_reclutador": c.notas_reclutador,
    }


@router.patch("/candidates/{external_id}/status")
def change_status(external_id: str, payload: StatusChange, db: Session = Depends(get_db)):
    repo = ATSRepository(db)
    c = repo.get_candidate_by_external_id(external_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidato no encontrado")

    updated = repo.update_candidate_status(c, payload.nuevo_estado, payload.changed_by, payload.motivo)
    return {"external_id": updated.external_id, "status": updated.status.value}


@router.post("/candidates/{external_id}/notes")
def add_note(external_id: str, nota: str, db: Session = Depends(get_db)):
    repo = ATSRepository(db)
    c = repo.get_candidate_by_external_id(external_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidato no encontrado")
    repo.append_candidate_note(c, nota)
    return {"nota_agregada": True}


@router.post("/candidates/{external_id}/star-evaluation", status_code=201)
def create_star_evaluation(
    external_id: str, payload: StarEvaluationCreate, db: Session = Depends(get_db)
):
    repo = ATSRepository(db)
    star_svc = StarInterviewService()
    c = repo.get_candidate_by_external_id(external_id)
    if not c:
        raise HTTPException(status_code=404, detail="Candidato no encontrado")

    for ev in payload.evaluaciones:
        errors = star_svc.validate_evaluation(ev.model_dump())
        if errors:
            raise HTTPException(status_code=400, detail="; ".join(errors))

    interview = repo.create_star_interview(
        c,
        payload.entrevistador,
        [e.model_dump() for e in payload.evaluaciones],
        payload.conclusion,
    )
    ficha = star_svc.render_ficha(interview, c.nombre)
    return {"interview_id": interview.id, "ficha": ficha}


@router.get("/positions/{external_id}/finalists-report")
def finalists_report(external_id: str, db: Session = Depends(get_db)):
    repo = ATSRepository(db)
    report_svc = ReportService()
    pos = repo.get_position_by_external_id(external_id)
    if not pos:
        raise HTTPException(status_code=404, detail="Vacante no encontrada")

    finalists = repo.get_finalists(pos.id)
    try:
        report = report_svc.render_executive_report(pos, finalists)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"reporte": report, "total_finalistas": len(finalists)}


@router.post("/integrations/schedule-interview")
def integration_schedule(payload: ScheduleInterviewPayload, db: Session = Depends(get_db)):
    """
    Webhook de integración ATS → Calendario.
    Se dispara cuando un candidato pasa a 'Entrevista Presencial'.
    """
    from app.models.database import InterviewType
    from app.services.calendar import CalendarService

    repo = ATSRepository(db)
    calendar = CalendarService()

    cand_data = payload.candidato
    interviewer = payload.entrevistador
    event_details = payload.detalles_evento

    c = repo.get_candidate_by_external_id(cand_data["id"])
    if not c:
        raise HTTPException(status_code=404, detail=f"Candidato {cand_data['id']} no encontrado")

    slots = calendar.get_available_slots(
        interviewer["email_corporativo"],
        interviewer.get("id_calendario", "primary"),
    )

    return {
        "candidato": cand_data,
        "entrevistador": interviewer,
        "detalles_evento": event_details,
        "disponibilidad": slots,
        "mensaje": "Consulta de disponibilidad completada. Seleccione horario para confirmar.",
    }
