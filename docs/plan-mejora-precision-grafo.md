# Plan: subir aciertos de categoría y subtipo

> **Estado: implementado y validado (Fases A-H completas).** Resultado final:
> categoría 94.7%→100% y subtipo 88.6%→95.5% sobre el CSV original de 113
> casos; categoría 88%→99% y subtipo 87.5%→98% sobre los 100 casos rurales.
> Detalle completo del resultado y de qué se dejó como limitación aceptada en
> `docs/validacion_100_casos_rurales.md`.

Basado en las 12 fallas de categoría y las causas explicadas en el chat
(ambigüedad por falta de contexto, negación no manejada, sustantivo fuerte
sin palabra de problema, señal débil de calle_tapada). Cada fase se implementa,
se valida contra `pytest tests/ -q`, `data/etiquetas_categoria.csv` (113 casos)
y `data/casos_prueba_rural_100.csv` (100 casos), y se documenta antes de pasar
a la siguiente. Regla del proyecto que se mantiene: si un caso no se arregla,
se documenta como limitación conocida en vez de forzar un parche frágil.

## Fase A — Separar "sustantivo de dominio" vs. "palabra de problema"

Reestructurar `vehiculo_o_contenedor_danado` y `basura_no_recolectable` en
`senales.py` en dos grupos: sustantivos que nombran el objeto (tolva, motor,
contenedor, basura...) y palabras que indican que algo anda mal (dañado,
desbordado, no sirve...). Ninguna categoría activa solo con un sustantivo de
dominio; necesita al menos una palabra de problema también presente.
Ataca la falla 5 (gato en la tolva, "sacó su basura a tiempo").
**Documentar**: qué palabras quedaron en cada grupo y por qué, y actualizar
el bloque de "Limitaciones conocidas" de `senales.py` quitando la 5 si se
resuelve.

## Fase B — Ampliar vocabulario de "palabra de problema" con sinónimos coloquiales

Para no perder recall en reportes cortos ("tolva rota", "motor malo"), sumar
a la lista de palabras de problema los sinónimos genéricos que la Fase A
necesita: roto, rota, malo, mala, feo, fea, "no sirve", "no jala", "no
prende", "no arranca", "se echo a perder", "ya no funciona". Se explica en el
plan que esta lista nunca será exhaustiva (limitación aceptada), pero cubre
los casos más comunes del habla coloquial rural.
**Documentar**: agregar una nota en `senales.py` explicando que esta lista es
deliberadamente amplia para compensar el recall perdido en la Fase A, y que
sigue siendo incompleta por diseño (no se puede enumerar todo el español
coloquial).

## Fase C — Disambiguación por proximidad (camión propio vs. vehículo ajeno; contenedor de basura vs. contenedor de carga)

Agregar patrones de ventana (regex con `.{0,N}` entre dos palabras) para
diferenciar:
- "camión/recolector" cerca de atoro/atasco/averió/descompuso →
  `vehiculo_o_contenedor_danado`.
- "carro/vehículo/coche" (ajeno) cerca de atoro/atasco/volcó/atravesado →
  `calle_tapada`.
- "contenedor de basura/comunitario/público" → `basura_no_recolectable`;
  "contenedor de carga/del camión" → `vehiculo_o_contenedor_danado`.

Ataca la falla 4 (atorado ambiguo) y parte de la falla 1 (contenedor
ambiguo). Se deja explícito que esto sigue siendo heurístico: reportes donde
el sujeto está lejos del verbo, o no se menciona "camión"/"carro" en
absoluto, van a seguir sin resolverse bien - se documenta como limitación
residual, no se promete resolverlo al 100%.
**Documentar**: cada patrón de ventana con un comentario explicando qué caso
real motivó agregarlo (igual que se ha hecho con cada fix anterior).

## Fase D — Manejo de negación con lista blanca

Antes de contar una señal, revisar si está precedida por "no"/"nunca"/"sin"
a un máximo de 3 palabras de distancia. Si es así, anular esa coincidencia
particular - EXCEPTO si la frase completa está en una lista blanca de
negaciones-que-sí-son-señal ("no se puede pasar", "no deja circular", "no se
puede cruzar", que ya cuentan como señal de bloqueo total). Ataca la falla
de negación ("no impide el paso", "no estorba el camino").
**Documentar**: la lista blanca completa y por qué cada frase está ahí (para
que quien mantenga esto después no la borre pensando que es un bug).

## Fase E — Promover "reparando/arreglando" + sustantivo de vía como señal débil de calle_tapada

Hoy "reparando"/"arreglando" solo alimentan `entidades.py` (vigencia), nunca
pueden ayudar a decidir la categoría porque se consultan después. Agregar un
patrón de ventana: "reparando/arreglando" cerca de un sustantivo de vía
(camino, calle, brecha, vado, puente, carretera, terracería) cuenta como
señal débil (+1) de `calle_tapada`. Sin el sustantivo de vía cerca, no cuenta
(para no activar con "están reparando la escuela"). Ataca la falla de señal
débil (fase 2, limitación documentada desde antes).
**Documentar**: por qué se exige el sustantivo de vía cerca y no basta con
la palabra sola.

## Fase F (opcional, no sube el score de aciertos por sí sola) — Marcar subtipo de baja confianza cuando no hay ninguna señal de entidad

Agregar funciones `hay_señal_severidad` / `hay_señal_vigencia` en
`entidades.py` que digan si de verdad hubo una pista (no solo el default
ciego). En `grafo.py`, si categoria es calle_tapada y ninguna de las dos tuvo
señal real, agregar un campo nuevo `subtipo_confiable: false` en la salida
(sin tocar el valor de `subtipo`, para no arriesgar el accuracy medido).
Esto no "sube aciertos" en el sentido estricto - es una mejora de
transparencia para que el backend sepa cuándo el subtipo es una adivinanza
conservadora y pueda, por ejemplo, pedir corroboración antes de actuar.
**Documentar**: dejar explícito en el plan y en el código que esta fase es
de transparencia, no de precisión, para no confundir métricas.

## Fase G — Revalidación

Después de cada fase (no solo al final): correr `pytest tests/ -q -p
no:cacheprovider` (deben seguir pasando las 57 pruebas o más si se agregan
nuevas), medir accuracy sobre `data/etiquetas_categoria.csv` (113 casos,
baseline 92% categoría/93% subtipo aislado) y sobre
`data/casos_prueba_rural_100.csv` (100 casos, baseline 88%/88%). Reportar el
delta real de cada fase, no solo el número final.

## Fase H — Documentación final

Actualizar el bloque de "Limitaciones conocidas" en `senales.py` y
`entidades.py` quitando lo que se haya resuelto y dejando solo lo que sigue
siendo limitación real. Actualizar `docs/validacion_100_casos_rurales.md`
con el nuevo accuracy y la lista de qué se resolvió vs. qué se dejó
documentado. Marcar cada fase de este plan como completada con la fecha y
el resultado medido.
