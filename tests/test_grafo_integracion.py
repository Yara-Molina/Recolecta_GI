import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "grafo_inferencia"))

from grafo import GrafoInferencia  # noqa: E402

CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "etiquetas_categoria.csv"


def _grafo():
    return GrafoInferencia()


def _filas_csv():
    with open(CSV_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_ejemplo_calle_tapada_total_en_reparacion():
    resultado = _grafo().inferir("la calle esta completamente cerrada por obra de pavimentacion")
    assert resultado["categoria"] == "calle_tapada"
    assert resultado["subtipo"] == "total_en_reparacion"
    assert resultado["accion"] == "block_edge"
    assert resultado["regla_aplicada"] == "r1"


def test_ejemplo_calle_tapada_parcial_temporal():
    resultado = _grafo().inferir("un carro mal estacionado obstruye parcialmente la calle sera un rato")
    assert resultado["categoria"] == "calle_tapada"
    assert resultado["subtipo"] == "parcial_temporal"
    assert resultado["accion"] == "inflate_weight"
    assert resultado["regla_aplicada"] == "r2"


def test_ejemplo_basura_no_recolectable():
    resultado = _grafo().inferir("el contenedor esta desbordado y no cabe mas basura")
    assert resultado["categoria"] == "basura_no_recolectable"
    assert resultado["subtipo"] is None
    assert resultado["accion"] == "marcar_mantenimiento"
    assert resultado["regla_aplicada"] == "r3"


def test_ejemplo_vehiculo_danado():
    resultado = _grafo().inferir("el camion recolector se descompuso a medio camino")
    assert resultado["categoria"] == "vehiculo_o_contenedor_danado"
    assert resultado["accion"] == "marcar_mantenimiento"
    assert resultado["regla_aplicada"] == "r4"


def test_ejemplo_otro_sin_accion():
    resultado = _grafo().inferir("todo tranquilo en la ruta de hoy sin novedades")
    assert resultado["categoria"] == "otro"
    assert resultado["accion"] == "none"
    assert resultado["regla_aplicada"] == "r5"


def test_reporte_vacio_no_truena():
    resultado = _grafo().inferir("")
    assert resultado["categoria"] == "otro"
    assert resultado["accion"] == "none"


def test_accuracy_categoria_sobre_csv_etiquetado():
    """Prueba de regresion: si esto baja de 0.85, alguien rompio senales.py
    o clasificador.py sin darse cuenta. Ver docs/plan-completo-grafo-inferencia.md
    (meta: >=80% de accuracy en la categoria principal)."""
    grafo = _grafo()
    filas = _filas_csv()
    correctas = sum(
        1 for row in filas if grafo.inferir(row["reporte"])["categoria"] == row["categoria_real"]
    )
    accuracy = correctas / len(filas)
    assert accuracy >= 0.85, f"accuracy={accuracy:.0%} (esperado >=85%)"


def test_accuracy_subtipo_sobre_csv_etiquetado():
    """Prueba de regresion solo sobre las filas de calle_tapada.

    OJO: este numero es mas bajo que el 93% que dio entidades.py aislado en
    la Fase 4, y es esperado, no un bug nuevo. entidades.py se probo alli
    asumiendo que la categoria ya era correcta (se filtraba por
    categoria_real). Aqui, de punta a punta, subtipo depende de DOS cosas:
    que clasificador.py haya acertado la categoria (92%) Y que entidades.py
    haya acertado severidad+vigencia (93% dado categoria correcta). Cuando
    la categoria predicha falla, "subtipo" queda en None y eso cuenta como
    error aunque entidades.py nunca haya llegado a evaluarse. El umbral
    aqui es mas bajo a proposito para reflejar ese efecto compuesto."""
    grafo = _grafo()
    filas = [f for f in _filas_csv() if f["categoria_real"] == "calle_tapada"]
    correctas = sum(
        1 for row in filas if grafo.inferir(row["reporte"])["subtipo"] == row["subtipo_real"]
    )
    accuracy = correctas / len(filas)
    assert accuracy >= 0.75, f"accuracy_subtipo={accuracy:.0%} (esperado >=75%)"
