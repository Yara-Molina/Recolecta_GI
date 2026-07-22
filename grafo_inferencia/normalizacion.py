"""Capa de normalizacion del grafo de conocimiento-inferencia.

Antes de que el texto llegue a senales.py, se le quitan acentos y se pasa a
minusculas. Esto importa porque un reporte real lo escribe una persona -
a veces con acentos ("batería", "reparación"), a veces sin ellos ("bateria",
"reparacion") - y los diccionarios de palabras clave estan escritos sin
acentos. Sin este paso, "bateria" (keyword) nunca hace match con "batería"
(lo que escribio la persona), porque son strings distintos.
"""

from __future__ import annotations

import re
import unicodedata


def quitar_acentos(texto: str) -> str:
    forma_nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in forma_nfkd if not unicodedata.combining(c))


def normalizar(texto: str) -> str:
    """minusculas + sin acentos. Usar esta version (no el texto crudo) para
    todo lo que sea deteccion de señales, clasificacion y extraccion de
    entidades. El texto crudo se sigue guardando tal cual para mostrarlo."""
    return quitar_acentos(str(texto or "").lower())


def tokenizar(texto: str) -> list[str]:
    """Tokeniza el texto YA normalizado (ver normalizar()). Mismo patron de
    tokens que modelo_reportes/aplicar_modelo.py, mas la normalizacion de
    acentos que ese modulo no hace."""
    return re.findall(r"\b\w+\b", normalizar(texto), flags=re.UNICODE)
