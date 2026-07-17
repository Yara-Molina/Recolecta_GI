import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "grafo_inferencia"))

from senales import detectar_senales  # noqa: E402


def tokenizar(texto: str) -> list[str]:
    """Mismo tokenizador que usa modelo_reportes/aplicar_modelo.py."""
    return re.findall(r"\b\w+\b", texto.lower(), flags=re.UNICODE)


def categoria_ganadora(texto: str) -> tuple[str, int]:
    tokens = tokenizar(texto)
    scores = detectar_senales(tokens, texto)
    ganadora = max(scores, key=scores.get)
    return ganadora, scores[ganadora]


# --- calle_tapada -----------------------------------------------------

def test_calle_tapada_bloqueo_total_por_obra():
    texto = "la calle esta completamente cerrada por obra de pavimentacion"
    ganadora, score = categoria_ganadora(texto)
    assert ganadora == "calle_tapada"
    assert score > 0


def test_calle_tapada_arbol_caido():
    texto = "arbol caido bloquea totalmente la calle sera por un rato mientras lo quitan"
    ganadora, _ = categoria_ganadora(texto)
    assert ganadora == "calle_tapada"


def test_calle_tapada_sinonimo_derrumbe():
    """Ejemplo 'dificil' del CSV: no usa keywords obvias como bloqueado/cerrado."""
    texto = "un derrumbe de tierra impide el paso de vehiculos por completo"
    ganadora, score = categoria_ganadora(texto)
    assert ganadora == "calle_tapada"
    assert score > 0


# --- basura_no_recolectable --------------------------------------------

def test_basura_contenedor_desbordado():
    texto = "el contenedor esta desbordado y no cabe mas basura"
    ganadora, _ = categoria_ganadora(texto)
    assert ganadora == "basura_no_recolectable"


def test_basura_sinonimo_porqueria():
    texto = "hay muchisima porqueria acumulada que nadie recoge"
    ganadora, score = categoria_ganadora(texto)
    assert ganadora == "basura_no_recolectable"
    assert score > 0


# --- vehiculo_o_contenedor_danado --------------------------------------

def test_vehiculo_camion_descompuesto():
    texto = "el camion recolector se descompuso a medio camino"
    ganadora, _ = categoria_ganadora(texto)
    assert ganadora == "vehiculo_o_contenedor_danado"


def test_vehiculo_sinonimo_ruido_raro():
    texto = "el camion hace un ruido extrano en el motor cada vez que arranca"
    ganadora, score = categoria_ganadora(texto)
    assert ganadora == "vehiculo_o_contenedor_danado"
    assert score > 0


# --- otro (ninguna senal deberia activarse con fuerza) -----------------

def test_otro_sin_senales_fuertes():
    texto = "todo tranquilo en la ruta de hoy sin novedades"
    tokens = tokenizar(texto)
    scores = detectar_senales(tokens, texto)
    assert max(scores.values()) == 0


def test_otro_perro_no_activa_categorias():
    texto = "hay un perro callejero cerca del punto de recoleccion"
    tokens = tokenizar(texto)
    scores = detectar_senales(tokens, texto)
    assert max(scores.values()) == 0
