# clasificador_reportes

Microservicio de clasificación simbólica de reportes de Recolecta: un grafo de conocimiento-inferencia (señales/keywords + reglas IF-THEN) que clasifica el texto de un reporte en una categoría (`calle_tapada`, `basura_no_recolectable`, `vehiculo_o_contenedor_danado`, `otro`) y sugiere una acción sobre el algoritmo genético de rutas.

Es un servicio independiente de `modelo_reportes` (el filtro de fraude por ML no supervisado) y de `algoritmo_genetico_rutas`. No depende de ninguno de los dos para funcionar; solo recibe texto por HTTP.

Ver el plan completo en `../modelo_reportes/docs/plan-completo-grafo-inferencia.md`.

## Estructura

```
api/            # FastAPI: config, db, models, schemas, routers, services
grafo_inferencia/  # lógica del grafo: señales, clasificador, entidades, reglas, orquestador
data/           # muestra etiquetada para validar el grafo
tests/          # pruebas unitarias e integración
```

## Cómo correr (una vez instalado)

```bash
cd clasificador_reportes
python -m venv .venv
.venv\Scripts\activate  # o source .venv/bin/activate en Linux/Mac
pip install -r api/requirements.txt
uvicorn api.main:app --reload --port 8001
```

Luego abrir `http://127.0.0.1:8001/docs` para ver la documentación interactiva (Swagger).

## Estado actual

Fase 0 (scaffolding) completa: la app corre y responde `/health`. Las demás fases (señales, clasificador, entidades, reglas, orquestador, endpoint `/clasificar`) se van agregando paso a paso — ver el checklist en el plan.
