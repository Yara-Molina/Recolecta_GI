import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "grafo_inferencia"))

from entidades import construir_subtipo, extraer_severidad, extraer_vigencia  # noqa: E402


def tok(texto: str) -> list[str]:
    return re.findall(r"\b\w+\b", texto.lower())


def test_severidad_alta_por_completamente():
    texto = "la calle esta completamente cerrada por obra de pavimentacion"
    assert extraer_severidad(tok(texto), texto) == "alta"


def test_severidad_media_por_parcialmente():
    texto = "obra parcial en la calle solo cerraron un carril"
    assert extraer_severidad(tok(texto), texto) == "media"


def test_severidad_default_media_sin_pistas():
    texto = "la calle esta cerrada por un arbol caido"
    assert extraer_severidad(tok(texto), texto) == "media"


def test_severidad_alta_por_frase_no_se_puede_pasar():
    """Caso encontrado probando el grafo con ejemplos nuevos: una frase sin
    ninguna palabra suelta de severidad, pero que claramente implica bloqueo
    total. Antes de este fix, extraer_severidad solo miraba palabras sueltas
    y esto daba "media" incorrectamente."""
    texto = "hay un socavon enorme y no se puede pasar por la calle juarez"
    assert extraer_severidad(tok(texto), texto) == "alta"


def test_severidad_alta_por_frase_impide_el_paso():
    texto = "un derrumbe de tierra impide el paso de vehiculos"
    assert extraer_severidad(tok(texto), texto) == "alta"


def test_vigencia_en_reparacion_por_cuadrilla():
    texto = "una cuadrilla esta arreglando el pavimento y bloquearon toda la calle"
    assert extraer_vigencia(tok(texto), texto) == "en_reparacion"


def test_vigencia_temporal_por_rato():
    texto = "arbol caido bloquea totalmente la calle sera por un rato mientras lo quitan"
    assert extraer_vigencia(tok(texto), texto) == "temporal"


def test_vigencia_default_en_reparacion_sin_pistas():
    texto = "la calle esta cerrada por un arbol caido"
    assert extraer_vigencia(tok(texto), texto) == "en_reparacion"


def test_vigencia_temporal_por_funeral():
    """Encontrado probando en vivo: un funeral/marcha/desfile bloquea la calle
    sin ninguna cuadrilla de reparacion de por medio - antes caia al default
    "en_reparacion" solo por falta de señales, lo cual es incorrecto para
    este tipo de evento que por naturaleza es temporal."""
    texto = "calle cerrada por funeral"
    assert extraer_vigencia(tok(texto), texto) == "temporal"


def test_vigencia_temporal_por_manifestacion():
    texto = "la calle esta bloqueada por una manifestacion"
    assert extraer_vigencia(tok(texto), texto) == "temporal"


def test_construir_subtipo_combinaciones():
    assert construir_subtipo("alta", "en_reparacion") == "total_en_reparacion"
    assert construir_subtipo("alta", "temporal") == "total_temporal"
    assert construir_subtipo("media", "en_reparacion") == "parcial_en_reparacion"
    assert construir_subtipo("media", "temporal") == "parcial_temporal"
