"""Datos de ejemplo para demostración del ATS."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.database import CandidateStatus, SessionLocal, init_db
from app.services.ats_repository import ATSRepository


def get_or_create_position(repo: ATSRepository, data: dict):
    existing = repo.get_position_by_external_id(data["external_id"])
    if existing:
        print(f"Vacante ya existe: {existing.external_id}")
        return existing
    position = repo.create_position(data)
    print(f"Vacante creada: {position.external_id}")
    return position


def get_or_create_finalist(repo, db, data: dict, conclusion: str):
    existing = repo.get_candidate_by_external_id(data["external_id"])
    if existing:
        print(f"Candidato ya existe: {existing.external_id} - {existing.nombre}")
        return existing

    c = repo.create_candidate(data)
    repo.update_candidate_status(c, CandidateStatus.FINALISTA, "seed", "Candidato de demostración")
    c.notas_reclutador = conclusion
    db.commit()
    print(f"Candidato creado: {c.external_id} - {c.nombre}")
    return c


def seed():
    init_db()
    db = SessionLocal()
    repo = ATSRepository(db)

    try:
        pos_dev = get_or_create_position(
            repo,
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
            },
        )

        get_or_create_position(
            repo,
            {
                "external_id": "POS-HR-002",
                "title": "Reclutador Senior",
                "department": "Recursos Humanos",
                "key_competencies": ["Negociación", "Liderazgo", "Adaptabilidad"],
                "hiring_manager_name": "Carlos Ruiz",
                "hiring_manager_email": "carlos.ruiz@empresa.com",
                "location": "Híbrido - Guadalajara",
            },
        )

        pos_sec = get_or_create_position(
            repo,
            {
                "external_id": "POS-SEC-003",
                "title": "Guardia de Seguridad / Vigilante",
                "department": "Seguridad Patrimonial",
                "description": (
                    "Vigilancia de instalaciones corporativas, control de accesos, rondines "
                    "y respuesta a incidentes en turnos rotativos (matutino, vespertino, nocturno)."
                ),
                "key_competencies": [
                    "Vigilancia y control de accesos",
                    "Manejo de crisis",
                    "Atención al visitante",
                    "Trabajo bajo presión",
                ],
                "salary_range_min": 12000,
                "salary_range_max": 16500,
                "currency": "MXN",
                "hiring_manager_name": "Ricardo Méndez",
                "hiring_manager_email": "ricardo.mendez@empresa.com",
                "location": "Planta Industrial - Nave 3, Zona Norte",
            },
        )

        dev_conclusion = (
            "Perfil muy sólido en la parte operativa que hace un excelente match "
            "cultural con los valores de transparencia del equipo."
        )

        dev_candidates = [
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

        for data in dev_candidates:
            get_or_create_finalist(repo, db, data, dev_conclusion)

        sec_candidates = [
            {
                "external_id": "CAND-9901",
                "nombre": "Miguel Herrera Ruiz",
                "email": "miguel.herrera@email.com",
                "telefono": "+525511112222",
                "puesto_actual": "Guardia de Seguridad",
                "empresa_actual": "Grupo Securitas México",
                "anos_experiencia": 8,
                "expectativa_salarial": 14500,
                "disponibilidad": "Inmediata",
                "fortalezas": [
                    "Certificación DC-3 en seguridad privada y curso de primeros auxilios vigente",
                    "Experiencia en control de accesos y CCTV en corporativos de alto tráfico",
                    "Evaluación STAR competente en Manejo de crisis (calificación 3/4)",
                ],
                "areas_oportunidad": [
                    "No ha trabajado turno nocturno en los últimos 2 años; requiere readaptación",
                ],
                "position_id": pos_sec.id,
            },
            {
                "external_id": "CAND-9902",
                "nombre": "José Ramírez Castro",
                "email": "jose.ramirez@email.com",
                "telefono": "+525522223333",
                "puesto_actual": "Vigilante",
                "empresa_actual": "Centro Comercial Plaza Norte",
                "anos_experiencia": 5,
                "expectativa_salarial": 13800,
                "disponibilidad": "2 semanas",
                "fortalezas": [
                    "Excelente trato al visitante y resolución de conflictos en piso",
                    "Disponibilidad para turnos rotativos incluyendo fines de semana",
                    "Referencias verificadas de supervisor anterior",
                ],
                "areas_oportunidad": [
                    "Experiencia limitada en plantas industriales; principalmente retail",
                ],
                "position_id": pos_sec.id,
            },
            {
                "external_id": "CAND-9903",
                "nombre": "Fernando Vega Morales",
                "email": "fernando.vega@email.com",
                "telefono": "+525533334444",
                "puesto_actual": "Elemento de Seguridad Privada",
                "empresa_actual": "Protección Industrial del Bajío",
                "anos_experiencia": 12,
                "expectativa_salarial": 16000,
                "disponibilidad": "1 mes",
                "fortalezas": [
                    "Ex elemento del Ejército Mexicano con honorable licenciamiento",
                    "Evaluación STAR sobresaliente en Trabajo bajo presión (calificación 4/4)",
                    "Experiencia en rondines perimetrales y protocolos de emergencia en planta",
                ],
                "areas_oportunidad": [
                    "Expectativa salarial en el tope del rango autorizado ($16,500)",
                ],
                "position_id": pos_sec.id,
            },
            {
                "external_id": "CAND-9904",
                "nombre": "Luis Antonio Torres",
                "email": "luis.torres@email.com",
                "telefono": "+525544445555",
                "puesto_actual": "Supervisor de Turno",
                "empresa_actual": "Seguridad Total SA de CV",
                "anos_experiencia": 10,
                "expectativa_salarial": 15200,
                "disponibilidad": "Inmediata",
                "fortalezas": [
                    "Ha coordinado equipos de hasta 6 guardias en turno nocturno",
                    "Conocimiento de bitácoras, reportes de novedades y normativa NOM-019-STPS",
                    "Vive a 15 minutos de la planta; bajo riesgo de impuntualidad",
                ],
                "areas_oportunidad": [
                    "Perfil con experiencia de supervisor; evaluar si acepta rol operativo sin mando",
                ],
                "position_id": pos_sec.id,
            },
        ]

        sec_conclusions = {
            "CAND-9901": (
                "Candidato confiable con sólida trayectoria en seguridad corporativa. "
                "Recomendado para turno matutino o vespertino."
            ),
            "CAND-9902": (
                "Perfil orientado al servicio con buena actitud. Ideal si se prioriza "
                "atención a visitantes y personal en accesos principales."
            ),
            "CAND-9903": (
                "El perfil más robusto en manejo de crisis y experiencia industrial. "
                "Prioridad alta si el turno incluye noches o zonas de alto riesgo."
            ),
            "CAND-9904": (
                "Candidato con potencial de crecimiento a líder de cuadrilla. "
                "Excelente opción si se busca alguien que eleve estándares del equipo."
            ),
        }

        for data in sec_candidates:
            get_or_create_finalist(
                repo, db, data, sec_conclusions[data["external_id"]]
            )

        print("\nSeed completado exitosamente.")

    except ValueError as e:
        print(f"Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
