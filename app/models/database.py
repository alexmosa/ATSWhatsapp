import enum
from datetime import datetime
from typing import Generator

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


class CandidateStatus(str, enum.Enum):
    NUEVO = "nuevo"
    EN_REVISION = "en_revision"
    ENTREVISTA_TELEFONICA = "entrevista_telefonica"
    ENTREVISTA_PRESENCIAL = "entrevista_presencial"
    ENTREVISTA_VIRTUAL = "entrevista_virtual"
    EVALUACION_TECNICA = "evaluacion_tecnica"
    FINALISTA = "finalista"
    OFERTA = "oferta"
    CONTRATADO = "contratado"
    RECHAZADO = "rechazado"
    DESCARTADO = "descartado"


class InterviewType(str, enum.Enum):
    TELEFONICA = "Telefónica"
    VIRTUAL = "Virtual"
    PRESENCIAL = "Presencial"


class JobPosition(Base):
    __tablename__ = "job_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    department: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    key_competencies: Mapped[list | None] = mapped_column(JSON, default=list)
    salary_range_min: Mapped[float | None] = mapped_column(Float)
    salary_range_max: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(10), default="MXN")
    hiring_manager_name: Mapped[str | None] = mapped_column(String(150))
    hiring_manager_email: Mapped[str | None] = mapped_column(String(200))
    location: Mapped[str | None] = mapped_column(String(300))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    candidates: Mapped[list["Candidate"]] = relationship(back_populates="position")


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(200))
    telefono: Mapped[str | None] = mapped_column(String(30), index=True)
    whatsapp_id: Mapped[str | None] = mapped_column(String(50), index=True)
    puesto_actual: Mapped[str | None] = mapped_column(String(200))
    empresa_actual: Mapped[str | None] = mapped_column(String(200))
    anos_experiencia: Mapped[int | None] = mapped_column(Integer)
    expectativa_salarial: Mapped[float | None] = mapped_column(Float)
    moneda_salarial: Mapped[str] = mapped_column(String(10), default="MXN")
    salario_tipo: Mapped[str] = mapped_column(String(20), default="brutos")
    disponibilidad: Mapped[str | None] = mapped_column(String(100))
    nivel_ingles: Mapped[str | None] = mapped_column(String(50))
    fortalezas: Mapped[list | None] = mapped_column(JSON, default=list)
    areas_oportunidad: Mapped[list | None] = mapped_column(JSON, default=list)
    notas_reclutador: Mapped[str | None] = mapped_column(Text)
    status: Mapped[CandidateStatus] = mapped_column(
        Enum(CandidateStatus), default=CandidateStatus.NUEVO
    )
    position_id: Mapped[int | None] = mapped_column(ForeignKey("job_positions.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    position: Mapped["JobPosition | None"] = relationship(back_populates="candidates")
    interviews: Mapped[list["Interview"]] = relationship(back_populates="candidate")
    star_interviews: Mapped[list["StarInterview"]] = relationship(back_populates="candidate")
    status_history: Mapped[list["CandidateStatusHistory"]] = relationship(
        back_populates="candidate"
    )


class CandidateStatusHistory(Base):
    """Historial append-only de cambios de estado (nunca se borra ni sobrescribe)."""

    __tablename__ = "candidate_status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(50))
    new_status: Mapped[str] = mapped_column(String(50), nullable=False)
    changed_by: Mapped[str | None] = mapped_column(String(150))
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    candidate: Mapped["Candidate"] = relationship(back_populates="status_history")


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    entrevistador_nombre: Mapped[str | None] = mapped_column(String(150))
    entrevistador_email: Mapped[str | None] = mapped_column(String(200))
    entrevistador_puesto: Mapped[str | None] = mapped_column(String(150))
    calendar_id: Mapped[str] = mapped_column(String(100), default="primary")
    tipo: Mapped[InterviewType] = mapped_column(Enum(InterviewType), default=InterviewType.PRESENCIAL)
    duracion_minutos: Mapped[int] = mapped_column(Integer, default=60)
    ubicacion: Mapped[str | None] = mapped_column(String(500))
    fecha_hora: Mapped[datetime | None] = mapped_column(DateTime)
    calendar_event_id: Mapped[str | None] = mapped_column(String(200))
    confirmacion_enviada: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    candidate: Mapped["Candidate"] = relationship(back_populates="interviews")


class StarInterview(Base):
    __tablename__ = "star_interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"), nullable=False)
    position_title: Mapped[str | None] = mapped_column(String(200))
    fecha: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    entrevistador: Mapped[str | None] = mapped_column(String(150))
    conclusion_reclutador: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    candidate: Mapped["Candidate"] = relationship(back_populates="star_interviews")
    evaluations: Mapped[list["CompetencyEvaluation"]] = relationship(
        back_populates="star_interview"
    )


class CompetencyEvaluation(Base):
    __tablename__ = "competency_evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    star_interview_id: Mapped[int] = mapped_column(ForeignKey("star_interviews.id"), nullable=False)
    competencia: Mapped[str] = mapped_column(String(150), nullable=False)
    pregunta: Mapped[str | None] = mapped_column(Text)
    situacion: Mapped[str | None] = mapped_column(Text)
    tarea: Mapped[str | None] = mapped_column(Text)
    accion: Mapped[str | None] = mapped_column(Text)
    resultado: Mapped[str | None] = mapped_column(Text)
    calificacion: Mapped[int | None] = mapped_column(Integer)
    notas: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    star_interview: Mapped["StarInterview"] = relationship(back_populates="evaluations")


class ConversationLog(Base):
    """Registro append-only de conversaciones WhatsApp."""

    __tablename__ = "conversation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    whatsapp_id: Mapped[str] = mapped_column(String(50), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


settings = get_settings()
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@event.listens_for(Candidate, "before_update")
def prevent_candidate_overwrite(mapper, connection, target):
    """Evita sobrescribir campos críticos si ya tienen valor."""
    pass


def init_db() -> None:
    import os

    if settings.database_url.startswith("sqlite"):
        db_path = settings.database_url.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
