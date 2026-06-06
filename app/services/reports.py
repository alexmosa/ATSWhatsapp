"""Generación de reportes ejecutivos de terna de candidatos."""

from pathlib import Path

from jinja2 import Template

from app.models.database import Candidate, JobPosition


class ReportService:
    def __init__(self):
        template_path = Path(__file__).parent.parent / "templates" / "executive_report.md"
        self.template = Template(template_path.read_text(encoding="utf-8"))

    def render_executive_report(
        self,
        position: JobPosition,
        candidates: list[Candidate],
    ) -> str:
        if not candidates:
            raise ValueError(
                "No hay candidatos finalistas registrados en el ATS para esta vacante. "
                "No se puede generar el reporte sin datos reales."
            )

        candidatos_data = []
        for c in candidates:
            candidatos_data.append(
                {
                    "nombre": c.nombre,
                    "puesto_actual": c.puesto_actual,
                    "empresa_actual": c.empresa_actual,
                    "anos_experiencia": c.anos_experiencia,
                    "expectativa_salarial": c.expectativa_salarial,
                    "moneda_salarial": c.moneda_salarial,
                    "salario_tipo": c.salario_tipo,
                    "disponibilidad": c.disponibilidad,
                    "fortalezas": c.fortalezas,
                    "areas_oportunidad": c.areas_oportunidad,
                    "notas_reclutador": c.notas_reclutador,
                }
            )

        return self.template.render(
            vacante=position.title,
            hiring_manager=position.hiring_manager_name or "Hiring Manager",
            candidatos=candidatos_data,
        )
