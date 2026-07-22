"""Capa de extraccion de entidades del grafo de conocimiento-inferencia.

Solo tiene sentido llamarla cuando la categoria ya elegida (clasificador.py)
es "calle_tapada" - las demas categorias no tienen subtipo. Extrae dos
entidades a partir de los mismos tokens que ya calculo senales.py:

- severidad: alta (bloqueo total) | media (bloqueo parcial)
- vigencia: temporal (se resuelve solo/rapido) | en_reparacion (obra en curso,
  probablemente dura mas)

subtipo = combinacion de ambas, ej. "total_en_reparacion", "parcial_temporal".
"""

from __future__ import annotations

import re

from senales import SEÑALES_SEVERIDAD, SEÑALES_VIGENCIA


def _activa(tokens_set: set[str], texto: str, cfg: dict) -> bool:
    """True si alguna keyword (palabra suelta) o regex (frase) de cfg aparece."""
    if tokens_set & cfg["keywords"]:
        return True
    return any(re.search(patron, texto, flags=re.IGNORECASE) for patron in cfg["regex"])


def extraer_severidad(tokens: list[str], texto: str = "") -> str:
    """alta si hay señal explicita de bloqueo total/urgente; si no, media.

    Ademas de palabras sueltas (SEÑALES_SEVERIDAD[...]["keywords"]) revisa
    frases completas contra "texto" (ej. "no se puede pasar" no tiene ninguna
    palabra individual que por si sola signifique bloqueo total).

    Default conservador: si el texto no da pistas de severidad, se asume
    "media" (parcial) en vez de "alta" (total) - es peor sobre-reaccionar
    (bloquear una calle que solo esta parcialmente afectada) que sub-
    reaccionar un poco, dado que "media" en las reglas (Fase 5) solo infla
    el costo de la arista en vez de cortarla por completo.
    """
    tokens_set = set(tokens)
    if _activa(tokens_set, texto, SEÑALES_SEVERIDAD["alta"]):
        return "alta"
    if _activa(tokens_set, texto, SEÑALES_SEVERIDAD["media"]):
        return "media"
    return "media"


def extraer_vigencia(tokens: list[str], texto: str = "") -> str:
    """en_reparacion si hay señal de obra/trabajo en curso; si no, temporal.

    Default conservador en el otro sentido: sin pistas, se asume
    "en_reparacion" (mas duradero) en vez de "temporal" (se resuelve solo) -
    para que el backend no descarte por TTL corto un bloqueo que en realidad
    puede durar. Ver 06-grafo-inferencia-backend.md, seccion de vigencia_ttl.
    """
    tokens_set = set(tokens)
    if _activa(tokens_set, texto, SEÑALES_VIGENCIA["en_reparacion"]):
        return "en_reparacion"
    if _activa(tokens_set, texto, SEÑALES_VIGENCIA["temporal"]):
        return "temporal"
    return "en_reparacion"


def construir_subtipo(severidad: str, vigencia: str) -> str:
    """total_en_reparacion | total_temporal | parcial_en_reparacion | parcial_temporal"""
    base = "total" if severidad == "alta" else "parcial"
    return f"{base}_{vigencia}"


def hay_señal_severidad(tokens: list[str], texto: str = "") -> bool:
    """True si el texto dio alguna pista real de severidad (alta o media),
    en vez de caer en el default conservador de extraer_severidad(). Sirve
    para que grafo.py (Fase F) pueda marcar el subtipo como poco confiable
    cuando NINGUNA entidad (ni severidad ni vigencia) tuvo señal real - a
    diferencia de extraer_severidad(), que siempre devuelve un string
    ("alta"/"media") aunque haya adivinado a ciegas."""
    tokens_set = set(tokens)
    return _activa(tokens_set, texto, SEÑALES_SEVERIDAD["alta"]) or _activa(
        tokens_set, texto, SEÑALES_SEVERIDAD["media"]
    )


def hay_señal_vigencia(tokens: list[str], texto: str = "") -> bool:
    """Equivalente a hay_señal_severidad() pero para vigencia."""
    tokens_set = set(tokens)
    return _activa(tokens_set, texto, SEÑALES_VIGENCIA["en_reparacion"]) or _activa(
        tokens_set, texto, SEÑALES_VIGENCIA["temporal"]
    )


# --- Validado contra data/etiquetas_categoria.csv (solo filas calle_tapada) ---
#
# Tras las mejoras de precision de la Fase A-E (ver senales.py y
# docs/plan-mejora-precision-grafo.md), subtipo end-to-end paso de 93% a
# 95.5% (42/44) sobre este CSV. El caso de "cerrada al cien por ciento" que
# antes fallaba por falta de esa frase en las palabras de severidad ya se
# arreglo (se agrego "al cien por ciento" a SEÑALES_SEVERIDAD). Quedan 2
# casos documentados como limitacion real, no bug:
# "un charco enorme no deja pasar bien por un lado de la calle" (la frase
# "no deja pasar" activa severidad alta aunque el reporte diga "por un lado",
# que sugiere parcial) y "la calle quedo atascada de autos por un choque
# menor" (sin ninguna palabra de vigencia, el default conservador
# "en_reparacion" no acierta que en realidad es "temporal"). No se agregan
# mas palabras sueltas para estos dos para no sobreajustar al CSV sintetico.
