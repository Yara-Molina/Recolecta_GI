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

from senales import SEÑALES_SEVERIDAD, SEÑALES_VIGENCIA


def extraer_severidad(tokens: list[str]) -> str:
    """alta si hay señal explicita de bloqueo total/urgente; si no, media.

    Default conservador: si el texto no da pistas de severidad, se asume
    "media" (parcial) en vez de "alta" (total) - es peor sobre-reaccionar
    (bloquear una calle que solo esta parcialmente afectada) que sub-
    reaccionar un poco, dado que "media" en las reglas (Fase 5) solo infla
    el costo de la arista en vez de cortarla por completo.
    """
    tokens_set = set(tokens)
    if tokens_set & SEÑALES_SEVERIDAD["alta"]:
        return "alta"
    if tokens_set & SEÑALES_SEVERIDAD["media"]:
        return "media"
    return "media"


def extraer_vigencia(tokens: list[str]) -> str:
    """en_reparacion si hay señal de obra/trabajo en curso; si no, temporal.

    Default conservador en el otro sentido: sin pistas, se asume
    "en_reparacion" (mas duradero) en vez de "temporal" (se resuelve solo) -
    para que el backend no descarte por TTL corto un bloqueo que en realidad
    puede durar. Ver 06-grafo-inferencia-backend.md, seccion de vigencia_ttl.
    """
    tokens_set = set(tokens)
    if tokens_set & SEÑALES_VIGENCIA["en_reparacion"]:
        return "en_reparacion"
    if tokens_set & SEÑALES_VIGENCIA["temporal"]:
        return "temporal"
    return "en_reparacion"


def construir_subtipo(severidad: str, vigencia: str) -> str:
    """total_en_reparacion | total_temporal | parcial_en_reparacion | parcial_temporal"""
    base = "total" if severidad == "alta" else "parcial"
    return f"{base}_{vigencia}"


# --- Validado contra data/etiquetas_categoria.csv (solo filas calle_tapada) ---
#
# subtipo (severidad + vigencia combinadas): 41/44 = 93%. Los 3 casos que
# fallan son el mismo tipo de limitacion que en senales.py: sin ninguna
# palabra de vigencia en el texto ("un charco enorme no deja pasar bien...",
# "la calle quedo atascada de autos por un choque menor"), el default
# conservador "en_reparacion" no siempre acierta si el caso real era
# "temporal". Y una frase con numero literal ("cerrada al cien por ciento")
# no la agarra la lista de palabras de severidad. Se documentan en vez de
# seguir agregando palabras sueltas para no sobreajustar al CSV sintetico.
