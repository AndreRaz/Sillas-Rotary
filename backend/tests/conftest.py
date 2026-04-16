"""
Shared test fixtures for Sillas Rotary API tests.

Uses a temporary SQLite database for each test session, ensuring
tests never touch the production database.
"""
import os
import shutil
import sqlite3
import pytest
from starlette.testclient import TestClient


# ---------------------------------------------------------------------------
# Test database path — created fresh per test session
# ---------------------------------------------------------------------------
_test_db_path = None


@pytest.fixture(scope="session")
def _session_db(tmp_path_factory):
    """Create a single test database for the entire session."""
    global _test_db_path
    tmp_dir = tmp_path_factory.mktemp("sillas_test")
    _test_db_path = str(tmp_dir / "test_sillas.db")

    import init_db

    conn = sqlite3.connect(_test_db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    for stmt in init_db.DDL:
        conn.execute(stmt)
    conn.commit()
    conn.close()

    yield _test_db_path

    # Cleanup
    if os.path.exists(_test_db_path):
        os.unlink(_test_db_path)


@pytest.fixture(autouse=True)
def _patch_db(_session_db, monkeypatch):
    """Patch sqlite3.connect to use the test database instead of 'sillas.db'."""
    original_connect = sqlite3.connect

    def _patched_connect(database, *args, **kwargs):
        if database == "sillas.db":
            return original_connect(_test_db_path, *args, **kwargs)
        return original_connect(database, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", _patched_connect)

    # Also patch in modules that already imported sqlite3.connect
    import database
    import init_db

    monkeypatch.setattr(database, "sqlite3", sqlite3)
    monkeypatch.setattr(init_db, "sqlite3", sqlite3)

    # Reset DB state for each test: delete all rows from all tables
    conn = sqlite3.connect(_test_db_path)
    conn.execute("PRAGMA foreign_keys = OFF")
    for table in ["solicitudes_tecnicas", "estudios_socioeconomicos",
                   "tutores", "beneficiarios", "capturistas"]:
        conn.execute(f"DELETE FROM {table}")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    conn.close()

    yield


@pytest.fixture
def client(_session_db):
    """FastAPI TestClient pointing to the test database."""
    from main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_capturista(client):
    """Create a sample capturista and return their data."""
    response = client.post("/api/login", json={"nombre": "Capturista Test"})
    assert response.status_code == 200
    return response.json()


@pytest.fixture
def sample_estudio(client, sample_capturista):
    """Create a sample estudio socioeconomico and return the response data."""
    payload = {
        "capturista_id": sample_capturista["capturista_id"],
        "beneficiario": {
            "nombre": "Beneficiario Test",
            "fecha_nacimiento": "2000-01-15",
            "diagnostico": "Parálisis cerebral",
            "calle": "Calle Test 123",
            "colonia": "Centro",
            "ciudad": "León",
            "telefonos": "4621234567",
        },
        "tutores": [
            {
                "numero_tutor": 1,
                "nombre": "Tutor Test",
                "edad": 45,
                "nivel_estudios": "Licenciatura",
                "estado_civil": "Casado",
                "num_hijos": 2,
                "vivienda": "Propia",
                "fuente_empleo": "Empleado",
                "antiguedad": "10 años",
                "ingreso_mensual": 12000.0,
                "tiene_imss": True,
                "tiene_infonavit": False,
            }
        ],
        "estudio": {
            "otras_fuentes_ingreso": "Ninguna",
            "monto_otras_fuentes": None,
            "tuvo_silla_previa": False,
            "como_obtuvo_silla": None,
            "elaboro_estudio": "Capturista Test",
            "fecha_estudio": "2026-04-15",
            "sede": "León",
            "status": "completo",
        },
    }
    response = client.post("/api/estudios", json=payload)
    assert response.status_code == 201
    return response.json()