# ATS WhatsApp — Agente de Reclutamiento Senior

Agente autónomo de reclutamiento por **WhatsApp** integrado con un **ATS** (Applicant Tracking System). Gestiona procesos de selección complejos, entrevistas STAR, reportes ejecutivos de terna y agendamiento de entrevistas presenciales con calendario corporativo.

## Capacidades del agente

- **Estrategia de contratación**: planes de atracción de talento alineados a objetivos comerciales.
- **Gestión de perfiles críticos**: búsqueda y evaluación de puestos C-Level y alta especialidad.
- **Consultoría interna**: asistencia a hiring managers en definición de perfiles.
- **Asesoría salarial**: análisis de mercado y cierre de ofertas.
- **Metodología STAR**: entrevistas por competencias con escala 1–4.
- **Reportes ejecutivos**: terna de finalistas lista para el gerente técnico.
- **Agendamiento**: flujo ATS → webhook → calendario (Google/Outlook).

## Reglas de comportamiento

| Regla | Implementación |
|-------|----------------|
| No inventar información | Solo consulta datos del ATS y la conversación |
| No borrar registros | Sin endpoints DELETE; historial append-only |
| No sobrescribir registros | Campos existentes protegidos; notas se agregan |
| No revelar que es IA | Persona de reclutador senior en todas las respuestas |

## Arquitectura

```
[WhatsApp / Twilio] ──webhook──> [Agente Reclutador] ──tools──> [ATS SQLite/PostgreSQL]
                                        │
                                        ├── STAR Interviews
                                        ├── Reportes Ejecutivos
                                        └── Google Calendar API
```

## Inicio rápido

### 1. Instalar dependencias

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus credenciales de Twilio y OpenAI
```

### 3. Cargar datos de demostración

```bash
python scripts/seed_data.py
```

Incluye finalistas de ejemplo para:
- `POS-DEV-001` — Desarrollador Full Stack Senior (3 candidatos)
- `POS-SEC-003` — Guardia de Seguridad / Vigilante (4 candidatos)

### 4. Iniciar servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Documentación interactiva: http://localhost:8000/docs

### Docker

```bash
docker compose up --build
```

## Configuración WhatsApp (Twilio)

1. Crear cuenta en [Twilio](https://www.twilio.com/) y activar WhatsApp Sandbox o número Business.
2. Configurar webhook entrante: `POST https://tu-dominio.com/webhooks/whatsapp`
3. Variables en `.env`:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_WHATSAPP_FROM`

## API del ATS

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/ats/positions` | Listar vacantes |
| POST | `/api/ats/positions` | Crear vacante |
| GET | `/api/ats/candidates` | Listar candidatos |
| POST | `/api/ats/candidates` | Registrar candidato |
| PATCH | `/api/ats/candidates/{id}/status` | Cambiar estado (con historial) |
| POST | `/api/ats/candidates/{id}/star-evaluation` | Registrar evaluación STAR |
| GET | `/api/ats/positions/{id}/finalists-report` | Reporte ejecutivo de terna |
| POST | `/api/ats/integrations/schedule-interview` | Webhook de agendamiento |

## Flujo de agendamiento presencial

1. Reclutador mueve candidato a estado `entrevista_presencial` en el ATS.
2. Webhook dispara consulta de disponibilidad del entrevistador.
3. Candidato elige horario (o reclutador lo asigna).
4. Sistema crea evento en calendario y envía confirmación con datos logísticos.

### Payload de integración

```json
{
  "candidato": {
    "id": "CAND-9821",
    "nombre": "Carlos Mendoza",
    "email": "carlos.mendoza@email.com"
  },
  "entrevistador": {
    "email_corporativo": "hiring.manager@empresa.com",
    "id_calendario": "primary"
  },
  "detalles_evento": {
    "tipo": "Presencial",
    "duracion_minutos": 60,
    "ubicación": "Oficina Central - Sala de Juntas A, Piso 4"
  }
}
```

## Metodología STAR

El agente evalúa hasta **3 competencias** por entrevista:

- **S**ituación — contexto y problema
- **T**area — responsabilidad del candidato
- **A**cción — pasos en primera persona
- **R**esultado — desenlace e impacto

Escala: 1 Deficiente · 2 En Desarrollo · 3 Competente · 4 Sobresaliente

## Estructura del proyecto

```
app/
├── agent/          # Persona, herramientas y orquestador
├── api/            # Webhooks WhatsApp y REST ATS
├── models/         # Esquema de base de datos
├── services/       # ATS, calendario, reportes, STAR
└── templates/      # Plantillas de entrevista y reportes
scripts/
└── seed_data.py    # Datos de demostración
```

## Licencia

MIT
