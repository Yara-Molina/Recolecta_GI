"""Capa de senales del grafo de conocimiento-inferencia.

Cuenta coincidencias de palabras clave y patrones regex por categoria sobre
el texto ya tokenizado de un reporte. No clasifica todavia (eso es
clasificador.py, Fase 3) - esta capa solo "activa" senales, igual que en el
ejemplo del profesor (signals: pattern -> candidate_class).

--- Historial de mejoras de precision (ver docs/plan-mejora-precision-grafo.md) ---
Tras validar con 100 reportes en tono rural realista (accuracy 79%/65%), se
identificaron 4 causas raiz de error y se implemento una mejora por cada una:

Fase A+B: "vehiculo_o_contenedor_danado" y "basura_no_recolectable" ya NO
activan solo con un sustantivo de dominio (tolva, basura, contenedor...) -
necesitan tambien una palabra que indique problema. Esto evita falsos
positivos como "un gato se subio a la tolva" o "saco su basura a tiempo".
Para no perder recall en reportes cortos ("tolva rota", "bateria
descargada"), la lista de "palabras de problema" se amplio con sinonimos
coloquiales (roto, malo, no jala, no prende, etc.) - ver PALABRAS_PROBLEMA_*.

Fase C: se agregaron patrones de ventana (regex con .{0,N} entre dos
palabras) para distinguir "el camion se atoro" (vehiculo_o_contenedor_danado)
de "un carro se atoro y bloquea el paso" (calle_tapada), y "contenedor de
carga del camion" (vehiculo) de "contenedor de basura" (basura). Sigue siendo
heuristico: si el sujeto esta lejos del verbo, puede seguir sin resolverse.

Fase D: manejo de negacion. Antes de contar una coincidencia (keyword o
regex), se revisa si esta precedida por "no"/"nunca"/"sin" a corta
distancia; si es asi, se ignora - EXCEPTO los patrones en
PATRONES_NEGACION_SEGURA, que ya son negaciones validas por si mismas
("no se puede pasar" SI es señal de bloqueo).

Fase E: "reparando"/"arreglando" ya no dependen solo de la capa de vigencia
para activar calle_tapada - si aparecen cerca de un sustantivo de via
(camino, calle, vado, puente, etc.) cuentan como señal debil de categoria.
"""

from __future__ import annotations

import re


# --- Palabras/frases de negacion que NO deben disparar el filtro de Fase D ---
# Estas ya SON la señal (contienen "no" mostrando bloqueo total), asi que si
# alguien escribe "no se puede pasar" no hay que anularla por tener "no".
PATRONES_NEGACION_SEGURA = {
    r"no se puede pasar",
    r"no se puede cruzar",
    r"no (se )?deja (pasar|circular|cruzar)",
    r"no (jala|prende|arranca|sirve|funciona)",
    r"ya no (jala|prende|arranca|sirve|funciona|quiere)\w*",
    r"no (ha|han) (pasado|recogido)\w*",
    r"no (lo|la|los|las) recogen\w*",
    r"no recogen\w*",
    r"no (cup[oa]|alcanzo)\w*",
}

_MARCADORES_NEGACION = {"no", "nunca", "sin"}


def _precedido_por_negacion_texto(texto: str, inicio: int, ventana_chars: int = 18) -> bool:
    """True si en los ultimos `ventana_chars` caracteres antes de `inicio` hay
    un marcador de negacion suelto (palabra completa, no substring)."""
    fragmento = texto[max(0, inicio - ventana_chars):inicio]
    return any(re.search(rf"\b{m}\b", fragmento) for m in _MARCADORES_NEGACION)


def _precedido_por_negacion_tokens(tokens: list[str], indice: int, ventana: int = 3) -> bool:
    inicio = max(0, indice - ventana)
    return any(t in _MARCADORES_NEGACION for t in tokens[inicio:indice])


def _contar_keywords(tokens: list[str], keywords: set[str]) -> int:
    """Cuenta keywords en `tokens`, ignorando las precedidas de negacion
    (Fase D). No aplica a PATRONES_NEGACION_SEGURA porque esas son frases
    (regex), no keywords sueltas."""
    total = 0
    for i, tok in enumerate(tokens):
        if tok in keywords and not _precedido_por_negacion_tokens(tokens, i):
            total += 1
    return total


def _contar_regex(texto: str, patrones: list[str]) -> int:
    """Cuenta matches de cada patron en `texto`, ignorando los precedidos de
    negacion (Fase D) salvo que el patron este en PATRONES_NEGACION_SEGURA."""
    total = 0
    for patron in patrones:
        es_seguro = patron in PATRONES_NEGACION_SEGURA
        for match in re.finditer(patron, texto, flags=re.IGNORECASE):
            if es_seguro or not _precedido_por_negacion_texto(texto, match.start()):
                total += 1
    return total


# --- calle_tapada: se deja con el esquema plano (keywords + regex) porque
# sus palabras ya son bastante especificas/no ambiguas por si solas (no se
# encontro en las pruebas el problema de "sustantivo sin palabra de
# problema" para esta categoria). ---
CALLE_TAPADA = {
    "keywords": {
        # OJO: "bloqueado/a", "cerrado/a", "colapsada", "intransitable" NO
        # estan aqui aunque son parte del vocabulario de esta categoria -
        # ya los cubre un regex de prefijo abajo (bloque\w*, cerr\w*,
        # colapsad\w*, intransitable). Tenerlos en los dos lados contaba la
        # misma coincidencia dos veces e inflaba el score sin razon.
        "cierre", "desvio", "obstruye", "obstruido", "obstruida", "escombro",
        "escombros", "arbol", "rama", "ramas", "poste", "postes", "cables",
        "cable", "socavon", "derrumbe", "atascada", "atascado", "carril",
        "impasable",
    },
    "regex": [
        r"bloque\w*",
        r"cerr\w*",          # cubre cerrado/cerrada/cerraron/cerrando (no solo el participio)
        r"colapsad\w*",      # colapsada/colapsado/colapsaron
        r"obra\w*",
        r"tap[oa]\w*",       # tapa/tapo/tapada/tapado/tapando/tapan
        r"bache\w*",         # bache/baches
        r"estorb\w*",        # estorba/estorban/estorbando
        r"ocupa\w*",         # "el camino esta ocupado", "un puesto ocupa medio camino"
        r"volc\w*",          # volco/volcado/volcaron: vehiculo volcado bloqueando el paso
        r"intransitable",
        r"no se puede pasar",
        r"no se puede cruzar",
        r"no (se )?deja (pasar|circular|cruzar)",
        r"impide el paso",
        # Fase C: un vehiculo AJENO (no el camion recolector) atorado/volcado
        # bloqueando el camino - distinto del camion propio descompuesto.
        r"(carro|vehiculo|coche)\w*.{0,25}(atoro|atasc\w*|volc\w*|atravesad\w*)",
        r"(atoro|atasc\w*|volc\w*|atravesad\w*).{0,25}(carro|vehiculo|coche)\w*",
        # Fase E: "reparando"/"arreglando"/"cuadrilla" solo cuentan como
        # señal de categoria (no solo de vigencia) si estan cerca de un
        # sustantivo de via - si no, "estan reparando la escuela" activaria
        # calle_tapada por error.
        r"(reparando|arreglando|reparacion|cuadrilla)\w*.{0,30}"
        r"(camino|calle|brecha|vado|puente|carretera|terraceria|vereda|drenaje)\w*",
        r"(camino|calle|brecha|vado|puente|carretera|terraceria|vereda|drenaje)\w*"
        r".{0,30}(reparando|arreglando|reparacion|cuadrilla)\w*",
    ],
}

# --- basura_no_recolectable y vehiculo_o_contenedor_danado: esquema de 3
# niveles (Fase A+B) para no activar solo con un sustantivo neutro:
#
# - "fuertes": palabras/frases que YA implican un problema por si solas
#   (ej. "desbordado", "averiado") - cuentan siempre, no necesitan pareja.
# - "sustantivos": nombran el objeto (ej. "tolva", "basura") - NO cuentan
#   solos, necesitan que tambien haya algo en "fuertes" o "debiles".
# - "debiles": palabras de problema demasiado genericas para contar solas
#   (ej. "malo", "no jala" podrian ser de cualquier cosa) - cuentan solo si
#   tambien hay un sustantivo (o una fuerte) presente.
BASURA_NO_RECOLECTABLE = {
    "fuertes": {
        # "desbordado/a" y "tirada/o" y "regada/o" NO estan aqui: ya los
        # cubren los regex de prefijo abajo (desbord\w*, tirad[ao]s?,
        # regad[ao]s?) - tenerlos duplicados en keywords inflaba el score.
        "keywords": {"lleno", "llenos", "apestando", "tiradero", "porqueria"},
        "regex": [
            r"desbord\w*", r"tirad[ao]s?", r"regad[ao]s?", r"repletos?", r"derraman\w*",
            r"acumulad\w*",         # "basura acumulada" (gap real: sin esto, "acumulada"
                                    # no contaba como problema y el reporte caia en "otro")
            r"amontona\w*",         # "la basura se esta amontonando"
            r"podrid\w*",           # "olor a basura podrida"
            r"no (cup[oa]|alcanzo)\w*",       # "no cupo/no alcanzo en el camion"
            r"no (ha|han) (pasado|recogido)\w*",  # "el camion no ha pasado", "no han recogido"
            r"no (lo|la|los|las) recogen\w*",     # "no la recogen"
            r"no recogen\w*",
        ],
    },
    "sustantivos": {
        "keywords": {"basura", "bolsas", "costales", "contenedor", "contenedores"},
        "regex": [],
    },
    "debiles": {
        "keywords": set(),
        "regex": [],
    },
}

VEHICULO_O_CONTENEDOR_DANADO = {
    "fuertes": {
        # "averia/averiado" ya los cubre "aver[ií]\w*"; "descompuesto" ya lo
        # cubre "descompuest\w*"; "ponchada/ponchado" ya los cubre "ponch\w*"
        # (nuevo, ver abajo) - no se repiten aqui para no duplicar el conteo.
        # "descompuso" SI se queda: es un conjugacion distinta (raiz
        # "descompus-", no "descompuest-") que el regex no cubre.
        "keywords": {"descompuso", "falla", "fallando", "desperfecto", "dano", "fuga"},
        "regex": [
            r"aver[ií]\w*",
            r"descompuest\w*",
            r"ponch\w*",          # ponchada/ponchado/poncho/poncharon (antes solo
                                  # las dos formas exactas, se perdia el preterito)
            r"pinchad\w*",
            r"danad\w*",
            r"dana(ron|ndo)\b",
            r"se (detuvo|paro|apago) de golpe",
            r"dej(o|aron) de (servir|funcionar)",  # bug: antes "dejaron?" solo
                                  # matcheaba "dejaro"/"dejaron", nunca "dejo"
                                  # (el caso mas comun: "el compactador dejo de funcionar")
            r"sobrecalent\w*",    # "el radiador se sobrecalento"
            r"se qued[oó] (varad[oa]|parad[oa])\w*",  # "se quedo parado/varado a medio camino"
            r"ruido (raro|extra[nñ]o)",
            r"se (le )?sali[oó] el aceite",     # fuga de aceite = señal fuerte de por si
            # Fase C: EL CAMION propio (no un carro ajeno) atorado/atascado
            # en lodo/barro - distinto de un vehiculo ajeno bloqueando la via.
            r"(camion|recolector)\w*.{0,30}(atoro|atasc\w*)",
            r"(atoro|atasc\w*).{0,30}(camion|recolector)\w*",
            # Fase C: "contenedor de carga/del camion" (parte del vehiculo)
            # vs. "contenedor de basura" (basura_no_recolectable).
            r"contenedor\w*.{0,20}(carga|camion)\w*",
            r"(carga|camion)\w*.{0,20}contenedor\w*",
        ],
    },
    "sustantivos": {
        "keywords": {
            "motor", "bateria", "llanta", "radiador", "frenos", "embrague",
            "diesel", "compactador", "tolva", "aceite",
        },
        "regex": [],
    },
    "debiles": {
        # Fase B: sinonimos coloquiales de "esta danado/no funciona" -
        # demasiado genericos para activar solos (un dia "malo" no es un
        # camion danado), pero validos junto a un sustantivo del vehiculo.
        # Lista deliberadamente no exhaustiva: el español coloquial tiene mas
        # formas de decir "ya no sirve" de las que cualquier lista cubre.
        "keywords": {
            "malo", "mala", "roto", "rota", "descargada", "descargado", "descargo",
        },
        "regex": [
            r"no (jala|prende|arranca|sirve|funciona)\w*",
            r"ya no (jala|prende|arranca|sirve|funciona|quiere)\w*",
            r"se echo a perder",
        ],
    },
}


def _score_plano(tokens: list[str], texto: str, cfg: dict) -> int:
    return _contar_keywords(tokens, cfg["keywords"]) + _contar_regex(texto, cfg["regex"])


def _score_niveles(tokens: list[str], texto: str, cfg: dict) -> int:
    fuertes = _score_plano(tokens, texto, cfg["fuertes"])
    sustantivos_crudo = _score_plano(tokens, texto, cfg["sustantivos"])
    debiles_crudo = _score_plano(tokens, texto, cfg["debiles"])

    # Sustantivo de dominio solo cuenta si hay algo (fuerte o debil) que
    # indique que ese objeto tiene un problema. Debil solo cuenta si hay
    # algo (fuerte o sustantivo) que le de contexto de a que se refiere.
    sustantivos = sustantivos_crudo if (fuertes > 0 or debiles_crudo > 0) else 0
    debiles = debiles_crudo if (fuertes > 0 or sustantivos_crudo > 0) else 0

    return fuertes + sustantivos + debiles


def detectar_senales(tokens: list[str], texto: str) -> dict[str, int]:
    """Cuenta coincidencias de keywords + regex por categoria.

    tokens: palabras del reporte ya tokenizadas (minusculas, sin puntuacion).
    texto: el texto completo (normalizado o crudo), usado para los regex
           porque algunos patrones cruzan varias palabras (ej. "no se puede pasar").

    Devuelve {categoria: score}. Un score de 0 significa que ninguna senal de
    esa categoria se activo.
    """
    return {
        "calle_tapada": _score_plano(tokens, texto, CALLE_TAPADA),
        "basura_no_recolectable": _score_niveles(tokens, texto, BASURA_NO_RECOLECTABLE),
        "vehiculo_o_contenedor_danado": _score_niveles(tokens, texto, VEHICULO_O_CONTENEDOR_DANADO),
    }


# Se mantiene por compatibilidad (otros modulos/tests podrian importar el
# dict viejo directamente); ahora se arma a partir de las estructuras de
# arriba para no duplicar el vocabulario en dos lugares.
SEÑALES_POR_CATEGORIA: dict[str, dict[str, object]] = {
    "calle_tapada": CALLE_TAPADA,
    "basura_no_recolectable": {
        "keywords": BASURA_NO_RECOLECTABLE["fuertes"]["keywords"]
        | BASURA_NO_RECOLECTABLE["sustantivos"]["keywords"],
        "regex": BASURA_NO_RECOLECTABLE["fuertes"]["regex"],
    },
    "vehiculo_o_contenedor_danado": {
        "keywords": VEHICULO_O_CONTENEDOR_DANADO["fuertes"]["keywords"]
        | VEHICULO_O_CONTENEDOR_DANADO["sustantivos"]["keywords"],
        "regex": VEHICULO_O_CONTENEDOR_DANADO["fuertes"]["regex"],
    },
}


# Entidades (entidades.py las usa): severidad y vigencia, sobre calle_tapada.
SEÑALES_SEVERIDAD = {
    "alta": {
        "keywords": {
            "urgente", "grave", "total", "completo", "completa", "completamente",
            "totalmente", "toda", "todo", "colapsada", "colapsado", "intransitable",
            "impasable",
        },
        "regex": [
            r"no se puede pasar",
            r"no se puede cruzar",
            r"no deja (pasar|circular|cruzar)",
            r"impide el paso",
            r"al cien por ciento",
        ],
    },
    "media": {
        "keywords": {"parcial", "parcialmente", "medio", "media"},
        "regex": [],
    },
}

SEÑALES_VIGENCIA = {
    "temporal": {
        "keywords": {
            "temporal", "momentaneo", "momentanea", "momentaneamente", "momento",
            "rato", "ahorita",
            "funeral", "manifestacion", "marcha", "desfile", "procesion",
            "protesta", "evento", "kermes", "fiesta", "feria", "por funeral",
            "caminando",
        },
        "regex": [],
    },
    "en_reparacion": {
        "keywords": {"reparacion", "reparando", "obra", "arreglando", "cuadrilla"},
        "regex": [],
    },
}


# --- Limitaciones conocidas ---
#
# 1) "Contenedor" sigue siendo parcialmente ambiguo entre basura_no_recolectable
#    y vehiculo_o_contenedor_danado. La Fase C agrega una señal fuerte para
#    "contenedor de carga/del camion" del lado de vehiculo, pero si el mismo
#    reporte tambien menciona "basura" cerca, basura_no_recolectable puede
#    seguir ganando por tener mas señales sumadas. No se fuerza mas porque
#    resolverlo del todo requeriria identificar de que contenedor se habla,
#    no solo contar palabras.
# 2) Reportes de calle_tapada con una señal de bloqueo MUY debil que ademas
#    diga explicitamente que se puede pasar ("se puede pasar con cuidado un
#    rato") pueden seguir sin activar la categoria - es correcto no forzarlo,
#    porque forzar activaria calle_tapada en reportes que en realidad dicen
#    que el paso SI es posible.
# 3) "Atascado"/"atorado" para un vehiculo AJENO lejos de la palabra
#    "carro"/"vehiculo" (ej. el conductor no la menciona explicitamente)
#    sigue sin poder distinguirse de forma confiable de un vehiculo propio.
# 4) Negacion (Fase D) usa una ventana de caracteres/tokens, no gramatica
#    real - una negacion muy lejos de la palabra que modifica (mas de ~3
#    palabras) puede no detectarse, y viceversa, un "no" de una oracion
#    anterior separada por punto podria alcanzar a anular algo en la
#    siguiente por error. Se acepta como aproximacion razonable, no perfecta.
# 5) La lista de PALABRAS_PROBLEMA/"debiles" coloquiales (Fase B) es
#    deliberadamente incompleta: el español rural tiene mas sinonimos de
#    "ya no sirve" de los que cualquier lista puede enumerar.
#
# Estas limitaciones se compensan parcialmente en clasificador.py (umbral de
# confianza) y sobre todo en reglas.py (la fuente del reporte y la
# corroboracion filtran falsos positivos antes de tocar el AG).
