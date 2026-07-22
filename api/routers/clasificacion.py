from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.db.session import get_db
from api.models.clasificacion import Clasificacion
from api.schemas.clasificacion import (
    ClasificacionCreate,
    ClasificacionListResponse,
    ClasificacionRead,
)
from api.services.clasificacion_service import ClasificacionService

router = APIRouter(tags=["Clasificacion"])
service = ClasificacionService()


@router.post(
    "/clasificar",
    response_model=ClasificacionRead,
    summary="Clasificar un reporte",
    description=(
        "Corre el grafo de conocimiento-inferencia sobre el texto de un reporte "
        "y persiste el resultado (categoria, subtipo, confianza, accion sugerida)."
    ),
)
def clasificar(request: ClasificacionCreate, db: Session = Depends(get_db)):
    try:
        resultado = service.clasificar(request)
        modelo = service.to_model(resultado)
        db.add(modelo)
        db.commit()
        db.refresh(modelo)
        return modelo
    except Exception as exc:  # pragma: no cover - defensiva
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get(
    "/clasificaciones",
    response_model=ClasificacionListResponse,
    summary="Consultar clasificaciones realizadas",
)
def listar_clasificaciones(
    tenant_id: int = Query(..., ge=1, description="Tenant (municipio) cuyas clasificaciones se quieren consultar. Obligatorio: sin esto se filtraria entre tenants."),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    total = (
        db.query(func.count(Clasificacion.id))
        .filter(Clasificacion.tenant_id == tenant_id)
        .scalar()
        or 0
    )
    items = (
        db.query(Clasificacion)
        .filter(Clasificacion.tenant_id == tenant_id)
        .order_by(Clasificacion.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return ClasificacionListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get(
    "/clasificaciones/{clasificacion_id}",
    response_model=ClasificacionRead,
    summary="Consultar una clasificacion por id",
)
def obtener_clasificacion(
    clasificacion_id: int,
    tenant_id: int = Query(..., ge=1, description="Tenant (municipio) dueno de la clasificacion consultada."),
    db: Session = Depends(get_db),
):
    obj = (
        db.query(Clasificacion)
        .filter(Clasificacion.id == clasificacion_id, Clasificacion.tenant_id == tenant_id)
        .first()
    )
    if obj is None:
        raise HTTPException(status_code=404, detail="Clasificacion no encontrada")
    return obj
