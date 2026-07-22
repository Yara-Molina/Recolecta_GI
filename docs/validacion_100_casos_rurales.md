# Validación con 100 reportes en tono rural realista

Este documento resume la prueba hecha con 100 reportes redactados como los
escribiría un ciudadano o conductor de una zona rural (lenguaje coloquial,
con y sin acentos, vocabulario como "brecha", "vado", "terracería", "ejido",
"lodazal"), y las mejoras de precisión implementadas después
(`docs/plan-mejora-precision-grafo.md`).

Los 100 casos con su resultado completo están en
`data/casos_prueba_rural_100.csv`.

## Resultado final (tras las Fases A-F del plan de mejora)

| Medición | Antes de las mejoras | Después |
|---|---|---|
| `etiquetas_categoria.csv` (113 casos) — categoría | 94.7% | **100%** |
| `etiquetas_categoria.csv` (113 casos) — subtipo | 88.6% | **95.5%** |
| `casos_prueba_rural_100.csv` (100 casos) — categoría | 88.0% | **99%** |
| `casos_prueba_rural_100.csv` (100 casos) — subtipo | 87.5% | **98%** |

Los 57 tests automáticos (`pytest tests/ -q`) siguen pasando sin cambios en
sus aserciones.

## Qué se hizo (resumen; detalle completo en el plan)

1. **Sustantivo de dominio + palabra de problema.** "tolva", "basura",
   "contenedor" ya no activan su categoría solos - necesitan también una
   palabra de problema (dañado, desbordado, acumulada, etc.). Evita falsos
   positivos como "un gato se subió a la tolva".
2. **Vocabulario coloquial ampliado** para no perder los reportes cortos que
   la Fase 1 podía dejar fuera (roto, malo, no jala, no prende, se echó a
   perder, amontonando, no han recogido, no cupo...).
3. **Disambiguación por proximidad**: "camión/recolector" cerca de
   atoro/atascó → vehículo dañado; "carro/vehículo" ajeno cerca de lo mismo →
   calle tapada; "contenedor de carga/camión" vs. "contenedor de basura".
4. **Manejo de negación**: "no impide el paso", "no estorba el camino" ya no
   activan la señal de bloqueo, salvo las frases que ya son negación-señal
   ("no se puede pasar", "no ha pasado el camión", etc.), que quedaron en
   una lista blanca explícita.
5. **Señal débil de calle_tapada por proximidad**: "reparando"/"arreglando"
   cerca de un sustantivo de vía (vado, puente, terracería...) ahora sí
   cuenta para la categoría, no solo para vigencia.
6. **Limpieza de un bug real de doble conteo**: varias palabras estaban
   como keyword exacta Y como parte de un regex de prefijo al mismo tiempo
   (ej. "descompuesto" + `descompuest\w*`), inflando el score sin querer.
   Al corregirlo se destaparon 5 casos del CSV original que fallaban por
   falta de una palabra fuerte real (acumulada, podrida, fuga, sobrecalentó,
   "dejó de funcionar" - este último era un bug de regex, `dejaron?` nunca
   matcheaba "dejó").
7. **Fase F (transparencia, no de precisión)**: nuevo campo
   `subtipo_confiable` en la salida del grafo - `false` cuando ni severidad
   ni vigencia tuvieron ninguna pista real (el subtipo devuelto es una
   suposición conservadora, no una lectura del texto). Este campo hoy solo
   vive en `grafo.inferir()`; falta conectarlo al modelo/schema de la API
   si se quiere exponerlo o persistirlo (no se tocó esa capa en esta pasada).

## Limitación que queda (1 de 100, aceptada a propósito)

"el arroyo creció tantito y moja parte del vado, se puede pasar con cuidado
un rato" sigue clasificando como "otro". No se fuerza porque el reporte dice
explícitamente que el paso SIGUE siendo posible - forzar calle_tapada aquí
generaría falsos positivos en reportes similares donde de verdad no hay
bloqueo, solo una molestia menor.
