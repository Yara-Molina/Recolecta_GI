from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ClasificacionCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "reporte": "la calle esta completamente cerrada por obra de pavimentacion",
                "tiempo": 15,
                "inferencia_id": 42,
                "origen": "conductor",
            }
        }
    )

    reporte: str = Field(..., min_length=1, description="Texto completo del reporte")
    tiempo: int | None = Field(default=None, ge=0, description="Minutos desde el ultimo reporte")
    inferencia_id: int | None = Field(
        default=None, description="Referencia externa a modelo_reportes (no es FK real)"
    )
    origen: str | None = Field(
        default=None,
        pattern="^(conductor|ciudadano)$",
        description="Quien genero el reporte, si se conoce",
    )


class ClasificacionRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "reporte": "la calle esta completamente cerrada por obra de pavimentacion",
                "tiempo": 15,
                "inferencia_id": 42,
                "origen": "conductor",
                "categoria": "calle_tapada",
                "subtipo": "total_en_reparacion",
                "confianza": 1.0,
                "severidad": "alta",
                "vigencia": "en_reparacion",
                "accion": "block_edge",
                "regla_aplicada": "r1",
                "senales_detectadas": {
                    "calle_tapada": 2,
                    "basura_no_recolectable": 0,
                    "vehiculo_o_contenedor_danado": 0,
                },
                "traza": {"nodes": [], "edges": []},
                "created_at": "2026-07-17T10:00:00",
            }
        },
    )

    id: int
    reporte: str
    tiempo: int | None
    inferencia_id: int | None
    origen: str | None
    categoria: str
    subtipo: str | None
    confianza: float
    severidad: str | None
    vigencia: str | None
    accion: str
    regla_aplicada: str | None
    senales_detectadas: dict[str, Any]
    traza: dict[str, Any]
    created_at: datetime


class ClasificacionListResponse(BaseModel):
    items: list[ClasificacionRead]
    total: int
    limit: int
    offset: int
