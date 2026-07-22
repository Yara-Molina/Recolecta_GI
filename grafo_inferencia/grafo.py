"""Orquestador del grafo de conocimiento-inferencia.

Junta las 4 capas ya construidas (senales, clasificador, entidades, reglas)
en un solo punto de entrada: GrafoInferencia.inferir(texto). Esta es la
clase que va a usar api/services/clasificacion_service.py en la Fase 7 -
se instancia una sola vez al arrancar el servicio (carga el JSON de reglas
una vez) y despues solo se llama .inferir(texto) por cada reporte.
"""

from __future__ import annotations

from pathlib import Path

from normalizacion import normalizar, tokenizar
from senales import detectar_senales
from clasificador import clasificar
from entidades import (
    construir_subtipo,
    extraer_severidad,
    extraer_vigencia,
    hay_señal_severidad,
    hay_señal_vigencia,
)
from reglas import cargar_reglas, evaluar_reglas
from traza import construir_traza


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "grafo_conocimiento.json"


class GrafoInferencia:
    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.reglas = cargar_reglas(self.config_path)

    def inferir(self, texto: str) -> dict:
        # texto_norm (sin acentos, minusculas) es lo que se usa para TODA la
        # deteccion de señales/entidades. texto (el original) solo se usa
        # para mostrarlo en la traza y se guarda tal cual en la BD.
        texto_norm = normalizar(texto)
        tokens = tokenizar(texto)
        scores = detectar_senales(tokens, texto_norm)
        categoria, confianza = clasificar(scores)

        severidad = vigencia = subtipo = None
        # Fase F (transparencia, no sube el accuracy medido): si categoria es
        # calle_tapada pero NINGUNA de las dos entidades tuvo una señal real
        # (ambas cayeron en su default conservador), el subtipo sigue
        # calculandose igual mas abajo, pero se marca subtipo_confiable=False
        # para que el backend sepa que es una suposicion, no una lectura del
        # texto, y pueda por ejemplo pedir corroboracion antes de actuar.
        subtipo_confiable = None
        if categoria == "calle_tapada":
            severidad = extraer_severidad(tokens, texto_norm)
            vigencia = extraer_vigencia(tokens, texto_norm)
            subtipo = construir_subtipo(severidad, vigencia)
            subtipo_confiable = hay_señal_severidad(tokens, texto_norm) or hay_señal_vigencia(
                tokens, texto_norm
            )

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
            "subtipo_confiable": subtipo_confiable,
            "confianza": confianza,
            "severidad": severidad,
            "vigencia": vigencia,
            "accion": resultado_regla["accion"],
            "regla_aplicada": resultado_regla["regla_id"],
            "senales_detectadas": scores,
            "traza": traza,
        }
