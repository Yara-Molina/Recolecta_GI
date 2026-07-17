import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "grafo_inferencia"))

from entidades import construir_subtipo, extraer_severidad, extraer_vigencia  # noqa: E402


def tok(texto: str) -> list[str]:
    return re.findall(r"\b\w+\b", texto.lower())


def test_severidad_alta_por_completamente():
    tokens = tok("la calle esta completamente cerrada por obra de pavimentacion")
    assert extraer_severidad(tokens) == "alta"


def test_severidad_media_por_parcialmente():
    tokens = tok("obra parcial en la calle solo cerraron un carril")
    assert extraer_severidad(tokens) == "media"


def test_severidad_default_media_sin_pistas():
    tokens = tok("la calle esta cerrada por un arbol caido")
    assert extraer_severidad(tokens) == "media"


def test_vigencia_en_reparacion_por_cuadrilla():
    tokens = tok("una cuadrilla esta arreglando el pavimento y bloquearon toda la calle")
    assert extraer_vigencia(tokens) == "en_reparacion"


def test_vigencia_temporal_por_rato():
    tokens = tok("arbol caido bloquea totalmente la calle sera por un rato mientras lo quitan")
    assert extraer_vigencia(tokens) == "temporal"


def test_vigencia_default_en_reparacion_sin_pistas():
    tokens = tok("la calle esta cerrada por un arbol caido")
    assert extraer_vigencia(tokens) == "en_reparacion"


def test_construir_subtipo_combinaciones():
    assert construir_subtipo("alta", "en_reparacion") == "total_en_reparacion"
    assert construir_subtipo("alta", "temporal") == "total_temporal"
    assert construir_subtipo("media", "en_reparacion") == "parcial_en_reparacion"
    assert construir_subtipo("media", "temporal") == "parcial_temporal"
