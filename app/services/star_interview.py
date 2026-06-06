"""Servicio de entrevistas STAR por competencias."""

from datetime import datetime
from pathlib import Path

from jinja2 import Template

from app.models.database import CompetencyEvaluation, StarInterview

CALIFICACION_LABELS = {
    1: "Deficiente",
    2: "En Desarrollo",
    3: "Competente (Perfil Buscado)",
    4: "Sobresaliente",
}

STAR_QUESTIONS = {
    "Liderazgo": (
        "Cuéntame sobre alguna ocasión en la que tuviste que entregar un proyecto crítico "
        "con un equipo dividido o con falta de recursos. ¿Qué hiciste y cuál fue el resultado?"
    ),
    "Resolución de Problemas": (
        "Descríbeme una situación en la que enfrentaste un problema complejo sin una solución "
        "obvia. ¿Cómo lo abordaste y qué resultado obtuviste?"
    ),
    "Negociación": (
        "Cuéntame de una vez que tuviste que negociar con un cliente, proveedor o stakeholder "
        "interno para llegar a un acuerdo beneficioso. ¿Qué estrategia usaste?"
    ),
    "Trabajo en Equipo": (
        "Describe una situación en la que colaboraste con personas de distintas áreas para "
        "lograr un objetivo común. ¿Cuál fue tu rol y el resultado?"
    ),
    "Adaptabilidad": (
        "Platícame de un momento en que un cambio inesperado alteró tus planes de trabajo. "
        "¿Cómo te adaptaste y qué aprendiste?"
    ),
    "Comunicación": (
        "Cuéntame de una ocasión en la que tuviste que comunicar una decisión difícil o "
        "información compleja a diferentes audiencias. ¿Cómo lo hiciste?"
    ),
}


class StarInterviewService:
    def __init__(self):
        template_path = Path(__file__).parent.parent / "templates" / "star_interview.md"
        self.template = Template(template_path.read_text(encoding="utf-8"))

    def get_suggested_question(self, competencia: str) -> str:
        return STAR_QUESTIONS.get(
            competencia,
            f"Cuéntame sobre una situación pasada donde demostraste {competencia.lower()}. "
            "¿Qué hiciste y cuál fue el resultado?",
        )

    def render_ficha(self, interview: StarInterview, candidato_nombre: str) -> str:
        evaluaciones = []
        for ev in interview.evaluations:
            evaluaciones.append(
                {
                    "competencia": ev.competencia,
                    "pregunta": ev.pregunta or self.get_suggested_question(ev.competencia),
                    "situacion": ev.situacion,
                    "tarea": ev.tarea,
                    "accion": ev.accion,
                    "resultado": ev.resultado,
                    "calificacion": ev.calificacion,
                    "calificacion_label": CALIFICACION_LABELS.get(ev.calificacion or 0, "Sin calificar"),
                }
            )

        return self.template.render(
            candidato=candidato_nombre,
            posicion=interview.position_title or "Sin posición asignada",
            fecha=interview.fecha.strftime("%d/%m/%Y"),
            entrevistador=interview.entrevistador or "Reclutador Senior",
            evaluaciones=evaluaciones,
            conclusion=interview.conclusion_reclutador,
        )

    def validate_evaluation(self, evaluation: dict) -> list[str]:
        errors = []
        if not evaluation.get("competencia"):
            errors.append("La competencia es obligatoria.")
        cal = evaluation.get("calificacion")
        if cal is not None and cal not in (1, 2, 3, 4):
            errors.append("La calificación debe ser entre 1 y 4.")
        return errors
