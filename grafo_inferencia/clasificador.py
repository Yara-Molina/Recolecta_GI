"""Capa de clasificacion del grafo de conocimiento-inferencia.

Toma los scores por categoria que ya calculo senales.py y decide UNA
categoria ganadora + una confianza. No mira el texto de nuevo, solo los
scores - por eso es una capa separada y facil de probar sola.
"""

from __future__ import annotations


# Umbral MINIMO de señal cruda (conteo de keywords/regex, no un porcentaje)
# para no caer en "otro". Si ninguna categoria junta al menos esta cantidad
# de coincidencias, se considera que no hay evidencia suficiente. Se calibra
# con la validacion de la Fase 11 sobre el CSV etiquetado - hoy en 1 porque
# con el diccionario actual ya da buena separacion (ver Fase 2).
UMBRAL_SENAL_MINIMA = 1


def clasificar(scores: dict[str, int]) -> tuple[str, float]:
    """Elige la categoria ganadora y su confianza.

    confianza = proporcion del score de la categoria ganadora sobre el total
    de señales activadas entre TODAS las categorias. Si solo una categoria
    tiene señales, confianza = 1.0. Si el score se reparte entre varias
    categorias (señales contradictorias), la confianza baja aunque la
    categoria ganadora tenga el score mas alto.

    Nota sobre empates: si dos categorias quedan con el mismo score, gana la
    que aparezca primero en SEÑALES_POR_CATEGORIA (senales.py) - hoy el orden
    es calle_tapada, basura_no_recolectable, vehiculo_o_contenedor_danado.
    Esto es una decision explicita, no un accidente: en un reporte real, un
    posible bloqueo de calle es mas costoso de ignorar que una confusion de
    categoria, asi que en un empate se prefiere no perder una señal de
    calle_tapada.
    """
    if not scores or max(scores.values()) < UMBRAL_SENAL_MINIMA:
        return "otro", 0.0

    categoria = max(scores, key=scores.get)
    total = sum(scores.values()) or 1
    confianza = scores[categoria] / total
    return categoria, confianza
