"""Datos de ejemplo para demostración del ATS."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import CandidateStatus, SessionLocal, init_db
from app.services.ats_repository import ATSRepository


def seed():
    init_db()
    db = SessionLocal()
    repo = ATSRepository(db)

    try:
        pos_dev = repo.create_position(
            {
                "external_id": "POS-DEV-001",
                "title": "Desarrollador Full Stack Senior",
                "department": "Tecnología",
                "description": "Liderar desarrollo de plataforma ATS con integración WhatsApp.",
                "key_competencies": ["Liderazgo", "Resolución de Problemas", "Comunicación"],
                "salary_range_min": 45000,
                "salary_range_max": 65000,
                "currency": "MXN",
                "hiring_manager_name": "María González",
                "hiring_manager_email": "maria.gonzalez@empresa.com",
                "location": "Oficina Central - CDMX",
            }
        )
        print(f"Vacante creada: {pos_dev.external_id}")

        pos_hr = repo.create_position(
            {
                "external_id": "POS-HR-002",
                "title": "Reclutador Senior",
                "department": "Recursos Humanos",
                "key_competencies": ["Negociación", "Liderazgo", "Adaptabilidad"],
                "hiring_manager_name": "Carlos Ruiz",
                "hiring_manager_email": "carlos.ruiz@empresa.com",
                "location": "Híbrido - Guadalajara",
            }
        )
        print(f"Vacante creada: {pos_hr.external_id}")

        candidates = [
            {
                "external_id": "CAND-9821",
                "nombre": "Carlos Mendoza",
                "email": "carlos.mendoza@email.com",
                "telefono": "+525512345678",
                "puesto_actual": "Desarrollador Senior",
                "empresa_actual": "TechCorp",
                "anos_experiencia": 7,
                "expectativa_salarial": 55000,
                "disponibilidad": "2 semanas",
                "nivel_ingles": "B2",
                "fortalezas": [
                    "Fuerte experiencia técnica en Python y FastAPI",
                    "Trayectoria estable (promedio de 3 años por empresa)",
                ],
                "areas_oportunidad": [
                    "Su nivel de inglés es intermedio-avanzado (B2), requiere soltarse al hablar",
                ],
                "position_id": pos_dev.id,
            },
            {
                "external_id": "CAND-9822",
                "nombre": "Ana López",
                "email": "ana.lopez@email.com",
                "telefono": "+525598765432",
                "puesto_actual": "Tech Lead",
                "empresa_actual": "StartupXYZ",
                "anos_experiencia": 9,
                "expectativa_salarial": 62000,
                "disponibilidad": "1 mes",
                "fortalezas": [
                    "Evaluación STAR sobresaliente en Negociación",
                    "Experiencia liderando equipos de 5+ personas",
                ],
                "areas_oportunidad": [
                    "Expectativa salarial en el límite superior del rango",
                ],
                "position_id": pos_dev.id,
            },
            {
                "external_id": "CAND-9823",
                "nombre": "Roberto Sánchez",
                "email": "roberto.sanchez@email.com",
                "puesto_actual": "Full Stack Developer",
                "empresa_actual": "FinTech SA",
                "anos_experiencia": 5,
                "expectativa_salarial": 48000,
                "disponibilidad": "Inmediata",
                "fortalezas": [
                    "Excelente match cultural con valores de transparencia",
                    "Dominio de React y Node.js",
                ],
                "areas_oportunidad": [
                    "No ha liderado equipos directamente, aunque sí ha coordinado proyectos transversales",
                ],
                "position_id": pos_dev.id,
            },
        ]

        for data in candidates:
            c = repo.create_candidate(data)
            repo.update_candidate_status(
                c, CandidateStatus.FINALISTA, "seed", "Candidato de demostración"
            )
            c.notas_reclutador = (
                "Perfil muy sólido en la parte operativa que hace un excelente match "
                "cultural con los valores de transparencia del equipo."
            )
            db.commit()
            print(f"Candidato creado: {c.external_id} - {c.nombre}")

        print("\nSeed completado exitosamente.")

    except ValueError as e:
        print(f"Datos ya existen o error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
