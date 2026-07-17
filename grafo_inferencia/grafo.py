"""Orquestador del grafo de conocimiento-inferencia.

Junta las 4 capas ya construidas (senales, clasificador, entidades, reglas)
en un solo punto de entrada: GrafoInferencia.inferir(texto). Esta es la
clase que va a usar api/services/clasificacion_service.py en la Fase 7 -
se instancia una sola vez al arrancar el servicio (carga el JSON de reglas
una vez) y despues solo se llama .inferir(texto) por cada reporte.
"""

from __future__ import annotations

import re
from pathlib import Path

from senales import detectar_senales
from clasificador import clasificar
from entidades import construir_subtipo, extraer_severidad, extraer_vigencia
from reglas import cargar_reglas, evaluar_reglas
from traza import construir_traza


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "grafo_conocimiento.json"


def tokenizar(texto: str) -> list[str]:
    """Mismo tokenizador que usa modelo_reportes/aplicar_modelo.py
    (extraer_caracteristicas_reporte) - se copia aqui porque este es un
    servicio independiente y no debe importar codigo de otro repo."""
    return re.findall(r"\b\w+\b", str(texto or "").lower(), flags=re.UNICODE)


class GrafoInferencia:
    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.reglas = cargar_reglas(self.config_path)

    def inferir(self, texto: str) -> dict:
        tokens = tokenizar(texto)
        scores = detectar_senales(tokens, texto)
        categoria, confianza = clasificar(scores)

        severidad = vigencia = subtipo = None
        if categoria == "calle_tapada":
            severidad = extraer_severidad(tokens)
            vigencia = extraer_vigencia(tokens)
            subtipo = construir_subtipo(severidad, vigencia)

        hechos = {"categoria": categoria, "severidad": severidad, "vigencia": vigencia}
        resultado_regla = evaluar_reglas(self.reglas, hechos)

        traza = construir_traza(
            texto=texto,
            tokens=tokens,
            senales_detectadas=scores,
            categoria=categoria,
            confianza=confianza,
            severidad=severidad,
            vigencia=vigencia,
            accion=resultado_regla["accion"],
            regla_aplicada=resultado_regla["regla_id"],
        )

        return {
            "categoria": categoria,
            "subtipo": subtipo,
            "confianza": confianza,
            "severidad": severidad,
            "vigencia": vigencia,
            "accion": resultado_regla["accion"],
            "regla_aplicada": resultado_regla["regla_id"],
            "senales_detectadas": scores,
            "traza": traza,
        }
