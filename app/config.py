from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "ATS WhatsApp Reclutamiento"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me"

    database_url: str = "sqlite:///./data/ats.db"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"

    google_calendar_credentials_file: str = "credentials/google_credentials.json"
    google_calendar_token_file: str = "credentials/google_token.json"

    webhook_base_url: str = "http://localhost:8000"

    default_recruiter_name: str = "Equipo de Atracción de Talento"
    default_company_name: str = "Tu Empresa"


@lru_cache
def get_settings() -> Settings:
    return Settings()
