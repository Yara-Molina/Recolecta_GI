import os
import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# DATABASE_URL se lee al importar api.db.session - hay que fijarla ANTES de
# importar api.main, y a un archivo temporal para no mezclar datos de prueba
# con la base de desarrollo (clasificador_reportes.db).
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    # El "with" es lo que dispara el evento de startup (Base.metadata.create_all).
    # Sin esto, TestClient(app) a secas nunca crea las tablas.
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_clasificar_calle_tapada_total(client):
    r = client.post(
        "/clasificar",
        json={
            "reporte": "la calle esta completamente cerrada por obra de pavimentacion",
            "tenant_id": 1,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["categoria"] == "calle_tapada"
    assert data["subtipo"] == "total_en_reparacion"
    assert data["accion"] == "block_edge"
    assert data["regla_aplicada"] == "r1"
    assert data["id"] > 0


def test_clasificar_guarda_origen_e_inferencia_id(client):
    r = client.post(
        "/clasificar",
        json={
            "reporte": "el contenedor esta desbordado y no cabe mas basura",
            "inferencia_id": 42,
            "origen": "conductor",
            "tenant_id": 1,
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["inferencia_id"] == 42
    assert data["origen"] == "conductor"
    assert data["categoria"] == "basura_no_recolectable"


def test_clasificar_rechaza_reporte_vacio(client):
    r = client.post("/clasificar", json={"reporte": "", "tenant_id": 1})
    assert r.status_code == 422


def test_clasificar_rechaza_origen_invalido(client):
    r = client.post(
        "/clasificar", json={"reporte": "algo", "origen": "vecino_curioso", "tenant_id": 1}
    )
    assert r.status_code == 422


def test_clasificar_rechaza_sin_tenant_id(client):
    # tenant_id es obligatorio (Fase 4 de multitenancy): sin RLS en esta
    # base, es el unico filtro de aislamiento entre tenants.
    r = client.post("/clasificar", json={"reporte": "algo sin tenant"})
    assert r.status_code == 422


def test_listar_clasificaciones_paginado(client):
    r = client.get("/clasificaciones?tenant_id=1&limit=1&offset=0")
    assert r.status_code == 200
    data = r.json()
    assert data["limit"] == 1
    assert len(data["items"]) <= 1
    assert data["total"] >= 2  # ya insertamos al menos 2 en pruebas anteriores


def test_listar_clasificaciones_requiere_tenant_id(client):
    r = client.get("/clasificaciones")
    assert r.status_code == 422


def test_obtener_clasificacion_por_id(client):
    creada = client.post(
        "/clasificar",
        json={"reporte": "el camion recolector se descompuso a medio camino", "tenant_id": 1},
    ).json()
    r = client.get(f"/clasificaciones/{creada['id']}?tenant_id=1")
    assert r.status_code == 200
    assert r.json()["categoria"] == "vehiculo_o_contenedor_danado"


def test_obtener_clasificacion_inexistente_404(client):
    r = client.get("/clasificaciones/999999?tenant_id=1")
    assert r.status_code == 404


def test_obtener_clasificacion_de_otro_tenant_404(client):
    # Caso central de Fase 5: una clasificacion creada bajo tenant 1 no debe
    # ser visible al consultarla como tenant 2.
    creada = client.post(
        "/clasificar",
        json={"reporte": "bache enorme junto a la escuela", "tenant_id": 1},
    ).json()
    r = client.get(f"/clasificaciones/{creada['id']}?tenant_id=2")
    assert r.status_code == 404


def test_listar_clasificaciones_no_mezcla_tenants(client):
    client.post("/clasificar", json={"reporte": "reporte de tenant 2 exclusivo", "tenant_id": 2})
    r = client.get("/clasificaciones?tenant_id=2&limit=50")
    assert r.status_code == 200
    data = r.json()
    assert all(item["tenant_id"] == 2 for item in data["items"])
