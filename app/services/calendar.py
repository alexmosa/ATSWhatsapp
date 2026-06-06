"""Integración con calendarios corporativos (Google Calendar / Outlook)."""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CalendarService:
    """
    Consulta disponibilidad y crea eventos en calendario corporativo.

    Soporta Google Calendar API (Opción C del flujo de integración).
    En modo desarrollo sin credenciales, retorna slots simulados.
    """

    def __init__(self):
        self._service = None
        self._initialized = False

    def _init_google_calendar(self) -> bool:
        if self._initialized:
            return self._service is not None

        self._initialized = True
        creds_path = Path(settings.google_calendar_credentials_file)
        token_path = Path(settings.google_calendar_token_file)

        if not creds_path.exists():
            logger.warning("Credenciales de Google Calendar no encontradas. Modo simulado activo.")
            return False

        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            SCOPES = ["https://www.googleapis.com/auth/calendar"]
            creds = None
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
                    creds = flow.run_local_server(port=0)
                token_path.parent.mkdir(parents=True, exist_ok=True)
                token_path.write_text(creds.to_json())

            self._service = build("calendar", "v3", credentials=creds)
            return True
        except Exception as e:
            logger.error("Error inicializando Google Calendar: %s", e)
            return False

    def get_available_slots(
        self,
        interviewer_email: str,
        calendar_id: str = "primary",
        days_ahead: int = 7,
        slot_duration_minutes: int = 60,
        business_hours: tuple[int, int] = (9, 18),
    ) -> list[dict[str, Any]]:
        """Retorna huecos libres del entrevistador."""
        if self._init_google_calendar():
            return self._get_google_slots(
                calendar_id, days_ahead, slot_duration_minutes, business_hours
            )
        return self._get_mock_slots(days_ahead, slot_duration_minutes, business_hours)

    def _get_google_slots(
        self,
        calendar_id: str,
        days_ahead: int,
        slot_duration: int,
        business_hours: tuple[int, int],
    ) -> list[dict[str, Any]]:
        now = datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = (now + timedelta(days=days_ahead)).isoformat() + "Z"

        events_result = (
            self._service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        busy_slots = []
        for event in events_result.get("items", []):
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
            busy_slots.append((datetime.fromisoformat(start.replace("Z", "")), datetime.fromisoformat(end.replace("Z", ""))))

        return self._compute_free_slots(now, days_ahead, slot_duration, business_hours, busy_slots)

    def _get_mock_slots(
        self,
        days_ahead: int,
        slot_duration: int,
        business_hours: tuple[int, int],
    ) -> list[dict[str, Any]]:
        now = datetime.utcnow()
        return self._compute_free_slots(now, days_ahead, slot_duration, business_hours, [])

    def _compute_free_slots(
        self,
        start: datetime,
        days_ahead: int,
        slot_duration: int,
        business_hours: tuple[int, int],
        busy_slots: list[tuple[datetime, datetime]],
    ) -> list[dict[str, Any]]:
        free = []
        for day_offset in range(1, days_ahead + 1):
            day = start.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=day_offset)
            if day.weekday() >= 5:
                continue
            for hour in range(business_hours[0], business_hours[1]):
                slot_start = day.replace(hour=hour, minute=0)
                slot_end = slot_start + timedelta(minutes=slot_duration)
                if any(slot_start < b_end and slot_end > b_start for b_start, b_end in busy_slots):
                    continue
                free.append(
                    {
                        "inicio": slot_start.isoformat(),
                        "fin": slot_end.isoformat(),
                        "label": slot_start.strftime("%A %d/%m/%Y %H:%M"),
                    }
                )
        return free[:10]

    def create_event(
        self,
        calendar_id: str,
        summary: str,
        start: datetime,
        end: datetime,
        location: str,
        attendees: list[str],
        description: str = "",
    ) -> dict[str, Any]:
        """Crea evento en calendario. Retorna dict con event_id."""
        if self._init_google_calendar():
            event = {
                "summary": summary,
                "location": location,
                "description": description,
                "start": {"dateTime": start.isoformat(), "timeZone": "America/Mexico_City"},
                "end": {"dateTime": end.isoformat(), "timeZone": "America/Mexico_City"},
                "attendees": [{"email": e} for e in attendees],
            }
            created = self._service.events().insert(calendarId=calendar_id, body=event, sendUpdates="all").execute()
            return {"event_id": created["id"], "html_link": created.get("htmlLink")}

        mock_id = f"mock-event-{start.strftime('%Y%m%d%H%M')}"
        logger.info("Evento simulado creado: %s", mock_id)
        return {"event_id": mock_id, "html_link": None, "simulated": True}
