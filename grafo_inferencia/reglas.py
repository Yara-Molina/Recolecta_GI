"""Motor de reglas del grafo de conocimiento-inferencia.

Lee la lista de reglas IF-THEN de config/grafo_conocimiento.json y las evalua
contra los "hechos" que ya calcularon las capas anteriores (categoria de
clasificador.py, severidad/vigencia de entidades.py). Es forward-chaining
simple: primera regla que matchea gana, en el orden en que aparecen en el
JSON - por eso el orden de las reglas en el JSON importa (ver el archivo:
las reglas de calle_tapada van antes que la generica de "otro").
"""

from __future__ import annotations

import json
from pathlib import Path


def cargar_reglas(config_path: Path) -> list[dict]:
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["rules"]


def evaluar_reglas(reglas: list[dict], hechos: dict) -> dict:
    """hechos = {"categoria": ..., "severidad": ..., "vigencia": ...} (severidad
    y vigencia pueden venir en None si la categoria no es calle_tapada).

    Una condicion de una regla solo se compara si esta presente en el "if"
    de esa regla - por eso r3/r4/r5 (que no mencionan severidad) matchean
    para cualquier severidad, incluida None.
    """
    for regla in reglas:
        condiciones = regla["if"]
        if all(hechos.get(clave) == valor for clave, valor in condiciones.items()):
            return {"regla_id": regla["id"], **regla["then"]}
    return {"regla_id": None, "accion": "none"}
