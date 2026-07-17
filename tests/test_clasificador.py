import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "grafo_inferencia"))

from clasificador import clasificar  # noqa: E402


def test_categoria_dominante_confianza_alta():
    scores = {"calle_tapada": 3, "basura_no_recolectable": 0, "vehiculo_o_contenedor_danado": 0}
    categoria, confianza = clasificar(scores)
    assert categoria == "calle_tapada"
    assert confianza == 1.0


def test_sin_senales_cae_en_otro():
    scores = {"calle_tapada": 0, "basura_no_recolectable": 0, "vehiculo_o_contenedor_danado": 0}
    categoria, confianza = clasificar(scores)
    assert categoria == "otro"
    assert confianza == 0.0


def test_diccionario_vacio_cae_en_otro():
    categoria, confianza = clasificar({})
    assert categoria == "otro"
    assert confianza == 0.0


def test_empate_prefiere_calle_tapada():
    """Empate deliberado: en caso de duda, no se debe perder una señal de calle_tapada."""
    scores = {"calle_tapada": 1, "basura_no_recolectable": 1, "vehiculo_o_contenedor_danado": 0}
    categoria, confianza = clasificar(scores)
    assert categoria == "calle_tapada"
    assert confianza == 0.5


def test_senales_contradictorias_bajan_confianza():
    """Aunque una categoria gane claramente, si hay ruido de otras la confianza baja."""
    scores = {"calle_tapada": 3, "basura_no_recolectable": 1, "vehiculo_o_contenedor_danado": 0}
    categoria, confianza = clasificar(scores)
    assert categoria == "calle_tapada"
    assert 0.0 < confianza < 1.0


def test_senal_unica_debil_si_alcanza_el_umbral():
    scores = {"calle_tapada": 0, "basura_no_recolectable": 1, "vehiculo_o_contenedor_danado": 0}
    categoria, confianza = clasificar(scores)
    assert categoria == "basura_no_recolectable"
    assert confianza == 1.0
