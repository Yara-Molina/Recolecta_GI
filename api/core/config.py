from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[2]

# Por defecto usamos SQLite para poder correr el servicio sin depender de
# tener MySQL levantado. En producción, exportar la variable de entorno
# DATABASE_URL apuntando a un schema PROPIO (no compartir el de modelo_reportes),
# por ejemplo: mysql+pymysql://root:root@localhost:3306/clasificador_reportes_db
DEFAULT_DATABASE_URL = f"sqlite:///{BASE_DIR / 'clasificador_reportes.db'}"


def get_database_url() -> str:
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url
    return DEFAULT_DATABASE_URL


APP_TITLE = "Clasificador de Reportes - Grafo de Inferencia"
APP_DESCRIPTION = (
    "Microservicio de clasificacion simbolica de reportes (senales + reglas IF-THEN). "
    "Recibe el texto de un reporte y devuelve categoria, subtipo, confianza y la "
    "accion sugerida sobre el algoritmo genetico de rutas."
)
APP_VERSION = "0.1.0"
