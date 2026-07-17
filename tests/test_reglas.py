import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "grafo_inferencia"))

from reglas import cargar_reglas, evaluar_reglas  # noqa: E402

CONFIG_PATH = Path(__file__).resolve().parents[1] / "grafo_inferencia" / "config" / "grafo_conocimiento.json"


def _reglas():
    return cargar_reglas(CONFIG_PATH)


def test_cargar_reglas_trae_las_5():
    reglas = _reglas()
    assert [r["id"] for r in reglas] == ["r1", "r2", "r3", "r4", "r5"]


def test_r1_calle_tapada_severidad_alta_block_edge():
    hechos = {"categoria": "calle_tapada", "severidad": "alta", "vigencia": "en_reparacion"}
    resultado = evaluar_reglas(_reglas(), hechos)
    assert resultado == {"regla_id": "r1", "accion": "block_edge"}


def test_r2_calle_tapada_severidad_media_inflate_weight():
    hechos = {"categoria": "calle_tapada", "severidad": "media", "vigencia": "temporal"}
    resultado = evaluar_reglas(_reglas(), hechos)
    assert resultado == {"regla_id": "r2", "accion": "inflate_weight"}


def test_r3_basura_marcar_mantenimiento():
    hechos = {"categoria": "basura_no_recolectable", "severidad": None, "vigencia": None}
    resultado = evaluar_reglas(_reglas(), hechos)
    assert resultado == {"regla_id": "r3", "accion": "marcar_mantenimiento"}


def test_r4_vehiculo_marcar_mantenimiento():
    hechos = {"categoria": "vehiculo_o_contenedor_danado", "severidad": None, "vigencia": None}
    resultado = evaluar_reglas(_reglas(), hechos)
    assert resultado == {"regla_id": "r4", "accion": "marcar_mantenimiento"}


def test_r5_otro_sin_accion():
    hechos = {"categoria": "otro", "severidad": None, "vigencia": None}
    resultado = evaluar_reglas(_reglas(), hechos)
    assert resultado == {"regla_id": "r5", "accion": "none"}


def test_orden_de_reglas_importa():
    """r1 y r2 comparten categoria=calle_tapada; el motor debe evaluar r1
    (severidad=alta) antes que r2 (severidad=media), no al reves."""
    reglas = _reglas()
    ids = [r["id"] for r in reglas if r["if"].get("categoria") == "calle_tapada"]
    assert ids.index("r1") < ids.index("r2")


def test_sin_match_devuelve_none():
    hechos = {"categoria": "categoria_inventada", "severidad": None, "vigencia": None}
    resultado = evaluar_reglas(_reglas(), hechos)
    assert resultado == {"regla_id": None, "accion": "none"}
