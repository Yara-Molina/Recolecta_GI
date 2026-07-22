# Ejemplos para probar `POST /clasificar`

Casos reales corridos contra el grafo tal como está hoy (no son hipotéticos, los ejecuté directamente). Úsalos para probar en Swagger (`/docs`), con `curl`, o para armar más casos de prueba en `tests/`.

Formato de entrada mínimo:

```json
{ "reporte": "texto del reporte aqui" }
```

Campos opcionales: `tiempo` (int), `inferencia_id` (int, referencia a `modelo_reportes`), `origen` (`"conductor"` o `"ciudadano"`). `confianza`, `id` y `created_at` varían en cada corrida real; aquí muestro los valores que dio esta ejecución como referencia.

---

## Casos normales (uno por subtipo/categoría)

### 1. Calle tapada — total, en reparación

**Entrada:** `"la calle esta completamente cerrada por obra de pavimentacion"`

**Salida esperada:**
```json
{
  "categoria": "calle_tapada",
  "subtipo": "total_en_reparacion",
  "confianza": 1.0,
  "severidad": "alta",
  "vigencia": "en_reparacion",
  "accion": "block_edge",
  "regla_aplicada": "r1"
}
```

### 2. Calle tapada — total, temporal

**Entrada:** `"arbol caido bloquea totalmente la calle sera por un rato mientras lo quitan"`

```json
{
  "categoria": "calle_tapada",
  "subtipo": "total_temporal",
  "confianza": 1.0,
  "severidad": "alta",
  "vigencia": "temporal",
  "accion": "block_edge",
  "regla_aplicada": "r1"
}
```

### 3. Calle tapada — parcial, en reparación

**Entrada:** `"obra parcial en la calle solo cerraron un carril"`

```json
{
  "categoria": "calle_tapada",
  "subtipo": "parcial_en_reparacion",
  "confianza": 1.0,
  "severidad": "media",
  "vigencia": "en_reparacion",
  "accion": "inflate_weight",
  "regla_aplicada": "r2"
}
```

### 4. Calle tapada — parcial, temporal

**Entrada:** `"un carro mal estacionado obstruye parcialmente la calle sera un rato"`

```json
{
  "categoria": "calle_tapada",
  "subtipo": "parcial_temporal",
  "confianza": 1.0,
  "severidad": "media",
  "vigencia": "temporal",
  "accion": "inflate_weight",
  "regla_aplicada": "r2"
}
```

### 5. Calle tapada — severidad por frase, no por palabra suelta

**Entrada:** `"no se puede pasar por esta calle sera nada mas un rato"`

```json
{
  "categoria": "calle_tapada",
  "subtipo": "total_temporal",
  "confianza": 1.0,
  "severidad": "alta",
  "vigencia": "temporal",
  "accion": "block_edge",
  "regla_aplicada": "r1"
}
```
*(Este es el caso que encontramos probando en vivo: "no se puede pasar" no tiene ninguna palabra suelta de severidad, se detecta por frase completa.)*

### 6. Basura no recolectable

**Entrada:** `"el contenedor esta desbordado y no cabe mas basura"`

```json
{
  "categoria": "basura_no_recolectable",
  "subtipo": null,
  "confianza": 1.0,
  "severidad": null,
  "vigencia": null,
  "accion": "marcar_mantenimiento",
  "regla_aplicada": "r3"
}
```

### 7. Vehículo o contenedor dañado

**Entrada:** `"el camion recolector se descompuso a medio camino"`

```json
{
  "categoria": "vehiculo_o_contenedor_danado",
  "subtipo": null,
  "confianza": 1.0,
  "severidad": null,
  "vigencia": null,
  "accion": "marcar_mantenimiento",
  "regla_aplicada": "r4"
}
```

### 8. Otro (sin categoría clara)

**Entrada:** `"todo tranquilo en la ruta de hoy sin novedades"`

```json
{
  "categoria": "otro",
  "subtipo": null,
  "confianza": 0.0,
  "severidad": null,
  "vigencia": null,
  "accion": "none",
  "regla_aplicada": "r5"
}
```

---

## Casos límite / limitaciones conocidas (para que no parezcan "fallas" al probar)

Estos NO están mal — son las limitaciones que ya documentamos en `senales.py` y `entidades.py`. Los incluyo para que si los pruebas y ves un resultado "raro", sepas que es esperado.

### 9. Ambigüedad entre categorías

**Entrada:** `"un carro descompuesto estorba parcialmente el paso momentaneamente"`

```json
{
  "categoria": "vehiculo_o_contenedor_danado",
  "confianza": 0.67,
  "accion": "marcar_mantenimiento",
  "regla_aplicada": "r4"
}
```
Debería ser `calle_tapada` (un carro ajeno bloqueando el paso), pero "descompuesto" activa más señales de `vehiculo_o_contenedor_danado` que "estorba" a `calle_tapada`. Revisa la `traza` de este caso para ver por qué (dos señales activas, gana la de mayor score).

### 10. Negación no detectada

**Entrada:** `"se vio una ambulancia pasar pero no bloqueo la ruta"`

```json
{
  "categoria": "calle_tapada",
  "accion": "inflate_weight",
  "regla_aplicada": "r2"
}
```
El texto dice explícitamente que NO bloqueó la ruta, pero la señal "bloqueo" se activa igual. Documentado en `senales.py` como limitación de negación — no se corrigió a la ligera porque frases como "no se puede pasar" también usan "no" y ahí sí es señal válida.

---

## Validación de entrada (errores esperados, HTTP 422)

```json
{ "reporte": "" }
```
Rechazado: `reporte` tiene `min_length=1`.

```json
{ "reporte": "algo", "origen": "vecino_curioso" }
```
Rechazado: `origen` solo acepta `"conductor"` o `"ciudadano"`.
