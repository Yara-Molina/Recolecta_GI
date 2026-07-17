"""Capa de trazabilidad del grafo de conocimiento-inferencia.

Construye, para UN caso concreto ya resuelto por GrafoInferencia.inferir(),
el mismo tipo de estructura nodes/edges que el "example_instance" del JSON
de configuracion (grafo_conocimiento.json) - pero generada dinamicamente a
partir del resultado real, no escrita a mano. Sirve para poder graficar o
explicar cualquier caso puntual sin tener que reconstruirlo manualmente,
por ejemplo para la entrega de la materia.
"""

from __future__ import annotations


EFECTO_POR_ACCION = {
    "block_edge": "arista mas cercana al reporte -> distancia=inf (corte duro)",
    "inflate_weight": "peso de la arista mas cercana multiplicado (bloqueo blando)",
    "marcar_mantenimiento": "se crea un ticket en el panel de mantenimiento",
    "none": "sin efecto sobre el grafo vial",
}


def construir_traza(
    *,
    texto: str,
    tokens: list[str],
    senales_detectadas: dict[str, int],
    categoria: str,
    confianza: float,
    severidad: str | None,
    vigencia: str | None,
    accion: str,
    regla_aplicada: str | None,
) -> dict:
    nodes: list[dict] = [
        {"id": "texto_raw", "layer": "texto", "label": texto},
        {"id": "texto_norm", "layer": "normalizacion", "label": f"tokens ({len(tokens)}): {tokens[:12]}"},
    ]
    edges: list[dict] = [
        {"from": "texto_raw", "to": "texto_norm", "relation": "normalize"},
    ]

    # Un nodo de senal por cada categoria que activo AL MENOS una coincidencia,
    # no solo la ganadora - asi se ve tambien cuando hubo senales rivales
    # (lo cual explica por que la confianza no siempre es 1.0).
    for cat, score in senales_detectadas.items():
        if score <= 0:
            continue
        cue_id = f"cue_{cat}"
        nodes.append({"id": cue_id, "layer": "senal", "label": f"señal candidata: {cat} (score={score})"})
        edges.append({"from": "texto_norm", "to": cue_id, "relation": "activates"})

    nodes.append(
        {"id": "class_final", "layer": "clasificacion", "label": f"clase: {categoria} (confianza={confianza:.2f})"}
    )
    if senales_detectadas.get(categoria, 0) > 0:
        edges.append({"from": f"cue_{categoria}", "to": "class_final", "relation": "supports"})

    if categoria == "calle_tapada":
        nodes.append({"id": "ent_severidad", "layer": "entidad", "label": f"severidad: {severidad}"})
        nodes.append({"id": "ent_vigencia", "layer": "entidad", "label": f"vigencia: {vigencia}"})
        edges.append({"from": "class_final", "to": "ent_severidad", "relation": "extracts"})
        edges.append({"from": "class_final", "to": "ent_vigencia", "relation": "extracts"})

    rule_label = f"dispara {regla_aplicada}" if regla_aplicada else "ninguna regla coincidio"
    nodes.append({"id": "rule_fired", "layer": "regla", "label": rule_label})
    edges.append({"from": "class_final", "to": "rule_fired", "relation": "rule_in"})
    if categoria == "calle_tapada":
        edges.append({"from": "ent_severidad", "to": "rule_fired", "relation": "rule_in"})

    nodes.append({"id": "action", "layer": "accion", "label": f"accion: {accion}"})
    edges.append({"from": "rule_fired", "to": "action", "relation": "concludes"})

    nodes.append({"id": "effect", "layer": "efecto", "label": EFECTO_POR_ACCION.get(accion, accion)})
    edges.append({"from": "action", "to": "effect", "relation": "effect"})

    return {"nodes": nodes, "edges": edges}
