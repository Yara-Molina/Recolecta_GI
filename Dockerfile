FROM python:3.11-slim

WORKDIR /app

# Instala dependencias primero (aprovecha cache de Docker)
COPY api/requirements.txt ./api/requirements.txt
RUN pip install --no-cache-dir -r api/requirements.txt

# Copia el resto del código (api/, grafo_inferencia/, data/, tests/, etc.)
COPY . .

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')" || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001"]
