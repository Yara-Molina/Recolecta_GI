import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "grafo_inferencia"))

from grafo import GrafoInferencia  # noqa: E402


def _ids(nodes):
    return [n["id"] for n in nodes]


def test_traza_calle_tapada_incluye_entidades_y_efecto():
    resultado = GrafoInferencia().inferir(
        "la calle esta completamente cerrada por obra de pavimentacion"
    )
    traza = resultado["traza"]
    ids = _ids(traza["nodes"])

    assert "texto_raw" in ids
    assert "texto_norm" in ids
    assert "cue_calle_tapada" in ids
    assert "class_final" in ids
    assert "ent_severidad" in ids
    assert "ent_vigencia" in ids
    assert "rule_fired" in ids
    assert "action" in ids
    assert "effect" in ids

    # el efecto debe describir el corte de arista, no un texto generico
    effect_node = next(n for n in traza["nodes"] if n["id"] == "effect")
    assert "inf" in effect_node["label"]

    # la arista texto_norm -> cue_calle_tapada debe existir
    edges = {(e["from"], e["to"]) for e in traza["edges"]}
    assert ("texto_norm", "cue_calle_tapada") in edges
    assert ("cue_calle_tapada", "class_final") in edges


def test_traza_otro_no_incluye_entidades():
    resultado = GrafoInferencia().inferir("todo tranquilo en la ruta de hoy sin novedades")
    ids = _ids(resultado["traza"]["nodes"])
    assert "ent_severidad" not in ids
    assert "ent_vigencia" not in ids
    # sin ninguna senal activada, no deberia haber nodos "cue_*"
    assert not any(i.startswith("cue_") for i in ids)


def test_traza_es_serializable_a_json():
    import json

    resultado = GrafoInferencia().inferir("el camion recolector se descompuso a medio camino")
    # si esto no explota, es JSON-serializable (necesario para la columna JSON)
    json.dumps(resultado["traza"], ensure_ascii=False)
