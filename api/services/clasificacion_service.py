from __future__ import annotations

import sys

from api.core.config import BASE_DIR
from api.models.clasificacion import Clasificacion
from api.schemas.clasificacion import ClasificacionCreate

# grafo_inferencia/ usa imports "planos" (from senales import ...) en vez de
# imports relativos de paquete, para poder probarse aislado con
# sys.path.insert (ver tests/test_*.py). Aqui hacemos lo mismo antes de
# importar GrafoInferencia, para no tener que reescribir esos modulos.
GRAFO_DIR = BASE_DIR / "grafo_inferencia"
if str(GRAFO_DIR) not in sys.path:
    sys.path.insert(0, str(GRAFO_DIR))

from grafo import GrafoInferencia  # noqa: E402


class ClasificacionService:
    def __init__(self):
        self.grafo = GrafoInferencia()

    def clasificar(self, request: ClasificacionCreate) -> dict:
        resultado = self.grafo.inferir(request.reporte)
        return {
            "reporte": request.reporte,
            "tiempo": request.tiempo,
            "inferencia_id": request.inferencia_id,
            "origen": request.origen,
            "tenant_id": request.tenant_id,
            **resultado,
        }

    @staticmethod
    def to_model(payload: dict) -> Clasificacion:
        return Clasificacion(
            tenant_id=payload["tenant_id"],
            reporte=payload["reporte"],
            tiempo=payload.get("tiempo"),
            inferencia_id=payload.get("inferencia_id"),
            origen=payload.get("origen"),
            categoria=payload["categoria"],
            subtipo=payload["subtipo"],
            confianza=payload["confianza"],
            severidad=payload["severidad"],
            vigencia=payload["vigencia"],
            accion=payload["accion"],
            regla_aplicada=payload["regla_aplicada"],
            senales_detectadas=payload["senales_detectadas"],
            traza=payload["traza"],
        )
