"""
Tests for the socioeconomico (study) endpoints.

Covers:
- C3: Draft resume (POST → GET → PATCH flow)
- C4/N1: NULL coercion for monto_otras_fuentes
- N5: estudio_id returned in response
- CRUD operations (POST, GET, PATCH)
"""
import pytest


class TestEstudioCreate:
    """POST /api/estudios — create a socioeconomic study."""

    def test_create_estudio_completo(self, client, sample_capturista):
        """Creating a complete study returns 201 with estudio_id and beneficiario_id."""
        payload = {
            "capturista_id": sample_capturista["capturista_id"],
            "beneficiario": {
                "nombre": "María López",
                "fecha_nacimiento": "1995-03-20",
                "diagnostico": "Distrofia muscular",
                "calle": "Av. Principal 456",
                "colonia": "Centro",
                "ciudad": "Irapuato",
                "telefonos": "4621112233",
            },
            "tutores": [
                {
                    "numero_tutor": 1,
                    "nombre": "José López",
                    "ingreso_mensual": 8500.0,
                    "tiene_imss": True,
                    "tiene_infonavit": False,
                }
            ],
            "estudio": {
                "elaboro_estudio": "Ana García",
                "fecha_estudio": "2026-04-15",
                "sede": "Irapuato",
                "tuvo_silla_previa": False,
                "status": "completo",
            },
        }
        response = client.post("/api/estudios", json=payload)
        assert response.status_code == 201
        data = response.json()
        # N5: estudio_id must be present
        assert "estudio_id" in data
        assert "beneficiario_id" in data
        assert data["status"] == "completo"

    def test_create_estudio_borrador(self, client, sample_capturista):
        """Creating a draft (borrador) returns estudio_id."""
        payload = {
            "capturista_id": sample_capturista["capturista_id"],
            "beneficiario": {
                "nombre": "Draft Person",
                "fecha_nacimiento": "2005-06-10",
                "diagnostico": "Condición de prueba",
                "calle": "Calle Draft",
                "colonia": "Colonia Draft",
                "ciudad": "León",
                "telefonos": "4620000000",
            },
            "tutores": [
                {
                    "numero_tutor": 1,
                    "nombre": "Tutor Draft",
                    "tiene_imss": False,
                    "tiene_infonavit": False,
                }
            ],
            "estudio": {
                "elaboro_estudio": "Draft Tester",
                "fecha_estudio": "2026-04-15",
                "sede": "León",
                "tuvo_silla_previa": False,
                "status": "borrador",
            },
        }
        response = client.post("/api/estudios", json=payload)
        assert response.status_code == 201
        assert response.json()["status"] == "borrador"
        assert "estudio_id" in response.json()


class TestEstudioGet:
    """GET /api/estudios/{id} — retrieve a study with beneficiario and tutores."""

    def test_get_existing_estudio(self, client, sample_estudio):
        """Getting an existing study returns full data."""
        estudio_id = sample_estudio["estudio_id"]
        response = client.get(f"/api/estudios/{estudio_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == estudio_id
        assert "beneficiario" in data
        assert "tutores" in data
        assert data["beneficiario"]["nombre"] == "Beneficiario Test"

    def test_get_nonexistent_estudio(self, client):
        """Getting a non-existent study returns 404."""
        response = client.get("/api/estudios/99999")
        assert response.status_code == 404


class TestEstudioPatch:
    """PATCH /api/estudios/{id} — update a study (draft resume)."""

    def test_update_estudio_status(self, client, sample_estudio):
        """C3: Updating a study from borrador to completo via PATCH."""
        estudio_id = sample_estudio["estudio_id"]
        response = client.patch(
            f"/api/estudios/{estudio_id}",
            json={"status": "completo"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "completo"

    def test_update_estudio_fields(self, client, sample_estudio):
        """C3: Updating specific fields via PATCH."""
        estudio_id = sample_estudio["estudio_id"]
        response = client.patch(
            f"/api/estudios/{estudio_id}",
            json={"sede": "Guanajuato", "otras_fuentes_ingreso": "Remesas"},
        )
        assert response.status_code == 200
        # Verify by GET
        get_response = client.get(f"/api/estudios/{estudio_id}")
        data = get_response.json()
        assert data["sede"] == "Guanajuato"
        assert data["otras_fuentes_ingreso"] == "Remesas"

    def test_patch_nonexistent_estudio(self, client):
        """Patching a non-existent study returns 404."""
        response = client.patch("/api/estudios/99999", json={"status": "completo"})
        assert response.status_code == 404


class TestNullCoercion:
    """C4/N1: Verify NULL is stored instead of 0.0/'' for optional fields."""

    def test_monto_otras_fuentes_stores_null(self, client, sample_capturista, _session_db):
        """monto_otras_fuentes should store NULL, not 0.0, when absent."""
        import sqlite3
        payload = {
            "capturista_id": sample_capturista["capturista_id"],
            "beneficiario": {
                "nombre": "Null Test",
                "fecha_nacimiento": "2000-01-01",
                "diagnostico": "Test",
                "calle": "Calle Test",
                "colonia": "Test",
                "ciudad": "León",
                "telefonos": "4620000000",
            },
            "tutores": [
                {
                    "numero_tutor": 1,
                    "nombre": "Tutor Null",
                    "tiene_imss": False,
                    "tiene_infonavit": False,
                }
            ],
            "estudio": {
                "elaboro_estudio": "Tester",
                "fecha_estudio": "2026-04-15",
                "sede": "León",
                "tuvo_silla_previa": False,
                "monto_otras_fuentes": None,
                "status": "completo",
            },
        }
        response = client.post("/api/estudios", json=payload)
        assert response.status_code == 201
        estudio_id = response.json()["estudio_id"]

        # Verify in DB that monto_otras_fuentes is NULL
        conn = sqlite3.connect(_session_db)
        row = conn.execute(
            "SELECT monto_otras_fuentes FROM estudios_socioeconomicos WHERE id = ?",
            (estudio_id,),
        ).fetchone()
        conn.close()
        assert row[0] is None, f"Expected NULL, got {row[0]}"

    def test_tutor_without_optional_fields_stores_null(self, client, sample_capturista, _session_db):
        """Optional tutor fields should store NULL when absent."""
        import sqlite3
        payload = {
            "capturista_id": sample_capturista["capturista_id"],
            "beneficiario": {
                "nombre": "Tutor Null Test",
                "fecha_nacimiento": "2010-05-05",
                "diagnostico": "Test",
                "calle": "Calle",
                "colonia": "Col",
                "ciudad": "León",
                "telefonos": "4620000000",
            },
            "tutores": [
                {
                    "numero_tutor": 1,
                    "nombre": "Tutor Minimal",
                    "tiene_imss": False,
                    "tiene_infonavit": False,
                    # edad, nivel_estudios, etc. are all None/optional
                }
            ],
            "estudio": {
                "elaboro_estudio": "Tester",
                "fecha_estudio": "2026-04-15",
                "sede": "León",
                "tuvo_silla_previa": False,
                "status": "completo",
            },
        }
        response = client.post("/api/estudios", json=payload)
        assert response.status_code == 201

        # Verify tutor optional fields are NULL
        conn = sqlite3.connect(_session_db)
        row = conn.execute(
            "SELECT edad, nivel_estudios, vivienda FROM tutores WHERE nombre = ?",
            ("Tutor Minimal",),
        ).fetchone()
        conn.close()
        assert row[0] is None  # edad
        assert row[1] is None  # nivel_estudios
        assert row[2] is None  # vivienda
