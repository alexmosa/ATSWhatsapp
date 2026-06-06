import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import ats, webhooks
from app.config import get_settings
from app.models.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Base de datos ATS inicializada")
    yield


app = FastAPI(
    title=settings.app_name,
    description="Agente de reclutamiento senior por WhatsApp con ATS integrado",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhooks.router)
app.include_router(ats.router)


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "docs": "/docs",
        "webhook_whatsapp": "/webhooks/whatsapp",
        "api_ats": "/api/ats",
    }
