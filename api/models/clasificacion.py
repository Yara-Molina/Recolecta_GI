from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from api.db.session import Base


class Clasificacion(Base):
    __tablename__ = "clasificaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    reporte: Mapped[str] = mapped_column(String(2000), nullable=False)
    tiempo: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # inferencia_id NO es una foreign key real: modelo_reportes es otro
    # servicio, con su propia base de datos (ver docs/plan-completo-grafo-inferencia.md,
    # seccion "Propiedad de los datos"). Es solo una referencia externa.
    inferencia_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    origen: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "conductor" | "ciudadano"

    categoria: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    subtipo: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confianza: Mapped[float] = mapped_column(Float, nullable=False)
    severidad: Mapped[str | None] = mapped_column(String(20), nullable=True)
    vigencia: Mapped[str | None] = mapped_column(String(20), nullable=True)
    accion: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    regla_aplicada: Mapped[str | None] = mapped_column(String(10), nullable=True)
    senales_detectadas: Mapped[dict] = mapped_column(JSON, nullable=False)
    traza: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
