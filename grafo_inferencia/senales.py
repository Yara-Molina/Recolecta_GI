"""Capa de senales del grafo de conocimiento-inferencia.

Cuenta coincidencias de palabras clave y patrones regex por categoria sobre
el texto ya tokenizado de un reporte. No clasifica todavia (eso es
clasificador.py, Fase 3) - esta capa solo "activa" senales, igual que en el
ejemplo del profesor (signals: pattern -> candidate_class).
"""

from __future__ import annotations

import re


# Cada categoria tiene un set de palabras clave (comparacion exacta contra
# los tokens ya normalizados) y una lista de patrones regex (para capturar
# variantes/prefijos que las keywords exactas no cubren, ej. "bloque\\w*"
# atrapa "bloqueado", "bloqueada", "bloqueo", etc. en un solo patron).
SEÑALES_POR_CATEGORIA: dict[str, dict[str, object]] = {
    "calle_tapada": {
        "keywords": {
            "bloqueado", "bloqueada", "cerrada", "cerrado", "cierre", "desvio",
            "obstruye", "obstruido", "obstruida", "escombro", "escombros",
            "arbol", "rama", "ramas", "poste", "postes", "cables", "cable", "socavon",
            "intransitable", "derrumbe", "atascada", "atascado", "colapsada",
            "carril",
        },
        "regex": [
            r"bloque\w*",
            r"cerr\w*",          # cubre cerrado/cerrada/cerraron/cerrando (no solo el participio)
            r"obra\w*",
            r"tapa\w*",          # tapa/tapada/tapado/tapando/tapan
            r"bache\w*",         # bache/baches
            r"estorb\w*",        # estorba/estorban/estorbando
            r"intransitable",
            r"no se puede pasar",
            r"impide el paso",
            r"no deja (pasar|circular)",
        ],
    },
    "basura_no_recolectable": {
        "keywords": {
            "basura", "bolsas", "costales", "contenedor", "contenedores",
            "desbordado", "desbordada", "tirada", "tirado", "regada", "regado",
            "lleno", "llenos", "apestando", "tiradero", "porqueria", "porqueria",
        },
        "regex": [
            r"desbord\w*",
            r"tirad[ao]s?",
            r"regad[ao]s?",
            r"repletos?",
            r"derraman\w*",
        ],
    },
    "vehiculo_o_contenedor_danado": {
        "keywords": {
            "averia", "averiado", "descompuesto", "descompuso", "falla",
            "fallando", "motor", "bateria", "llanta", "ponchada", "ponchado",
            "radiador", "frenos", "embrague", "diesel", "compactador", "tolva",
        },
        "regex": [
            r"aver[ií]\w*",      # averia/averiado/se averio (no solo el sustantivo)
            r"descompuest\w*",
            r"pinchad\w*",
            r"se (detuvo|paro|apago) de golpe",
            r"dejaron? de (servir|funcionar)",
            r"ruido (raro|extra[nñ]o)",
        ],
    },
}

# Entidades (Fase 4 las usa): severidad y vigencia, sobre calle_tapada.
SEÑALES_SEVERIDAD = {
    "alta": {
        "urgente", "grave", "total", "completo", "completa", "completamente",
        "totalmente", "toda", "todo", "colapsada", "colapsado", "intransitable",
    },
    "media": {"parcial", "parcialmente", "medio", "media"},
}

SEÑALES_VIGENCIA = {
    "temporal": {
        "temporal", "momentaneo", "momentanea", "momentaneamente", "rato",
        "ahorita",
    },
    "en_reparacion": {"reparacion", "reparando", "obra", "arreglando", "cuadrilla"},
}


def detectar_senales(tokens: list[str], texto: str) -> dict[str, int]:
    """Cuenta coincidencias de keywords + regex por categoria.

    tokens: palabras del reporte ya tokenizadas (minusculas, sin puntuacion).
    texto: el texto completo (normalizado o crudo), usado para los regex
           porque algunos patrones cruzan varias palabras (ej. "no se puede pasar").

    Devuelve {categoria: score}. Un score de 0 significa que ninguna senal de
    esa categoria se activo.
    """
    scores: dict[str, int] = {}
    tokens_set = set(tokens)

    for categoria, cfg in SEÑALES_POR_CATEGORIA.items():
        score = len(tokens_set & cfg["keywords"])
        for patron in cfg["regex"]:
            score += len(re.findall(patron, texto, flags=re.IGNORECASE))
        scores[categoria] = score

    return scores


# --- Limitaciones conocidas (validadas contra data/etiquetas_categoria.csv) ---
#
# Contando solo señales (sin clasificador.py ni reglas.py todavia) esta capa
# acierta 104/113 = 92% de la categoria "ganadora" sobre el CSV sintetico.
# Los 9 casos que fallan son limitaciones reales de un enfoque de
# palabras-clave/regex, no bugs sueltos:
#
# 1) Palabras ambiguas entre categorias: "contenedor" aparece tanto en
#    basura_no_recolectable (contenedor de basura desbordado) como en
#    vehiculo_o_contenedor_danado (contenedor de carga del camion) y hasta en
#    calle_tapada (un contenedor bloqueando la calle). El conteo de señales
#    no distingue el contexto, solo la palabra.
# 2) Reportes de calle_tapada sin ninguna palabra "fuerte" de bloqueo (solo
#    mencionan "reparando"/"arreglando"/"ocupan parte de"): esas palabras son
#    de la capa de vigencia (Fase 4), no de categoria, asi que aqui no alcanzan
#    a activar calle_tapada por si solas.
# 3) Negacion: "no bloqueo la ruta" activa la señal de "bloqueo" igual que si
#    dijera "si bloqueo". Esta capa no analiza negacion. OJO: no se puede
#    arreglar con un filtro simple de "ignorar si precede un 'no'", porque
#    frases como "no se puede pasar" tambien usan "no" y ahi SI es señal
#    valida de bloqueo. Requeriria manejo de negacion mas cuidadoso; se deja
#    documentado para una iteracion futura en vez de parchearlo a medias.
#
# Estas limitaciones se compensan parcialmente en clasificador.py (Fase 3,
# umbral de confianza) y sobre todo en reglas.py (Fase 5, donde la fuente del
# reporte y la corroboracion filtran falsos positivos antes de tocar el AG).
