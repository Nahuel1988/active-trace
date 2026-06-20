from __future__ import annotations

import uuid

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TenantScopedMixin

import enum


class TipoEvaluacion(str, enum.Enum):
    Parcial = "Parcial"
    TP = "TP"
    Coloquio = "Coloquio"
    Recuperatorio = "Recuperatorio"


class EstadoReserva(str, enum.Enum):
    Activa = "Activa"
    Cancelada = "Cancelada"


class Evaluacion(Base, TenantScopedMixin):
    __tablename__ = "evaluacion"

    materia_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("materia.id", ondelete="CASCADE"), nullable=False
    )
    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cohorte.id", ondelete="CASCADE"), nullable=False
    )
    tipo: Mapped[str] = mapped_column(String(32), nullable=False, default=TipoEvaluacion.Coloquio)
    instancia: Mapped[str] = mapped_column(String(255), nullable=False)
    dias_disponibles: Mapped[int] = mapped_column(Integer, nullable=False)
    candidatos: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    __table_args__ = (
        UniqueConstraint("tenant_id", "materia_id", "cohorte_id", "tipo", "instancia", name="uq_evaluacion_identidad"),
    )


class ReservaEvaluacion(Base, TenantScopedMixin):
    __tablename__ = "reserva_evaluacion"

    evaluacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluacion.id", ondelete="CASCADE"), nullable=False
    )
    alumno_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    fecha_hora: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    estado: Mapped[str] = mapped_column(String(16), nullable=False, default=EstadoReserva.Activa)


class ResultadoEvaluacion(Base, TenantScopedMixin):
    __tablename__ = "resultado_evaluacion"

    evaluacion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluacion.id", ondelete="CASCADE"), nullable=False
    )
    alumno_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    nota_final: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "evaluacion_id", "alumno_id", name="uq_resultado_evaluacion_tenant_evaluacion_alumno"),
    )
