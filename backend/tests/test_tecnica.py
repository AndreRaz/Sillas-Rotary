"""
Tests for the tecnica (technical request) endpoints.

Covers:
- C4: NULL storage for optional measurement fields (not 0.0)
- N1: NULL for entidad_solicitante and justificacion (not "")
- C3: Draft resume (POST → GET → PATCH flow)
- Photo upload validation
"""
import pytest
import io


class TestSolicitudCreate:
    """POST /api/solicitudes — create a technical request."""

    def test_create_solicitud_with_null_measurements(
        self, client, sample_capturista, sample_estudio, _session_db
    ):
        """C4: Optional measurements should store NULL, not 0.0."""
        import sqlite3

        payload = {
            "capturista_id": sample_capturista["capturista_id"],
            "beneficiario_id": sample_estudio["beneficiario_id"],
            "entorno": "Urbano / Interiores",
            "control_tronco": "Completo",
            "control_cabeza": "Independiente",
            # All measurements are null/absent
            "status": "borrador",
        }
        response = client.post("/api/solicitudes", json=payload)
        assert response.status_code == 201
        solicitud_id = response.json()["solicitud_id"]

        # Verify in DB that measurements are NULL, not 0.0
        conn = sqlite3.connect(_session_db)
        row = conn.execute(
            "SELECT altura_total_in, peso_kg, medida_cabeza_asiento "
            "FROM solicitudes_tecnicas WHERE id = ?",
            (solicitud_id,),
        ).fetchone()
        conn.close()
        assert row[0] is None, f"altura_total_in should be NULL, got {row[0]}"
        assert row[1] is None, f"peso_kg should be NULL, got {row[1]}"
        assert row[2] is None, f"medida_cabeza_asiento should be NULL, got {row[2]}"

    def test_create_solicitud_null_text_fields(
        self, client, sample_capturista, sample_estudio, _session_db
    ):
        """N1: entidad_solicitante and justificacion should store NULL, not ''."""
        import sqlite3

        payload = {
            "capturista_id": sample_capturista["capturista_id"],
            "beneficiario_id": sample_estudio["beneficiario_id"],
            "entorno": "Rural / Terreno irregular",
            "control_tronco": "Parcial / Requiere apoyo lateral",
            "control_cabeza": "Independiente",
            "status": "borrador",
        }
        response = client.post("/api/solicitudes", json=payload)
        assert response.status_code == 201
        solicitud_id = response.json()["solicitud_id"]

        conn = sqlite3.connect(_session_db)
        row = conn.execute(
            "SELECT entidad_solicitante, justificacion "
            "FROM solicitudes_tecnicas WHERE id = ?",
            (solicitud_id,),
        ).fetchone()
        conn.close()
        assert row[0] is None, f"entidad_solicitante should be NULL, got '{row[0]}'"
        assert row[1] is None, f"justificacion should be NULL, got '{row[1]}'"

    def test_create_solicitud_with_measurements(
        self, client, sample_capturista, sample_estudio
    ):
        """Creating a solicitud with measurements stores them correctly."""
        payload = {
            "capturista_id": sample_capturista["capturista_id"],
            "beneficiario_id": sample_estudio["beneficiario_id"],
            "entorno": "Mixto",
            "control_tronco": "Nulo / Requiere soporte total",
            "control_cabeza": "Intermitente",
            "observaciones_posturales": "Escoliosis leve",
            "altura_total_in": 45.5,
            "peso_kg": 70.0,
            "medida_cabeza_asiento": 25.0,
            "medida_hombro_asiento": 20.0,
            "medida_prof_asiento": 18.0,
            "medida_rodilla_talon": 16.0,
            "medida_ancho_cadera": 14.0,
            "entidad_solicitante": "DIF Guanajuato",
            "prioridad": "Alta",
            "justificacion": "Caso urgente",
            "status": "completo",
        }
        response = client.post("/api/solicitudes", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "completo"

    def test_create_solicitud_invalid_capturista_id(
        self, client, sample_estudio
    ):
        """Creating a solicitud with non-existent capturista_id returns 400."""
        payload = {
            "capturista_id": 99999,
            "beneficiario_id": sample_estudio["beneficiario_id"],
            "entorno": "Urbano / Interiores",
            "control_tronco": "Completo",
            "control_cabeza": "Independiente",
            "status": "borrador",
        }
        response = client.post("/api/solicitudes", json=payload)
        assert response.status_code == 400


class TestSolicitudGet:
    """GET /api/solicitudes/{id} — retrieve a technical request."""

    def test_get_existing_solicitud(
        self, client, sample_capturista, sample_estudio
    ):
        """Getting an existing solicitud returns full data."""
        payload = {
            "capturista_id": sample_capturista["capturista_id"],
            "beneficiario_id": sample_estudio["beneficiario_id"],
            "entorno": "Urbano / Interiores",
            "control_tronco": "Completo",
            "control_cabeza": "Independiente",
            "status": "borrador",
        }
        create_resp = client.post("/api/solicitudes", json=payload)
        solicitud_id = create_resp.json()["solicitud_id"]

        response = client.get(f"/api/solicitudes/{solicitud_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == solicitud_id
        assert data["entorno"] == "Urbano / Interiores"

    def test_get_nonexistent_solicitud(self, client):
        """Getting a non-existent solicitud returns 404."""
        response = client.get("/api/solicitudes/99999")
        assert response.status_code == 404


class TestSolicitudPatch:
    """PATCH /api/solicitudes/{id} — update a technical request (draft resume)."""

    def test_update_solicitud_status(
        self, client, sample_capturista, sample_estudio
    ):
        """C3: Updating a solicitud from borrador to completo via PATCH."""
        payload = {
            "capturista_id": sample_capturista["capturista_id"],
            "beneficiario_id": sample_estudio["beneficiario_id"],
            "entorno": "Rural / Terreno irregular",
            "control_tronco": "Nulo / Requiere soporte total",
            "control_cabeza": "No posee / Requiere cabezal",
            "status": "borrador",
        }
        create_resp = client.post("/api/solicitudes", json=payload)
        solicitud_id = create_resp.json()["solicitud_id"]

        patch_resp = client.patch(
            f"/api/solicitudes/{solicitud_id}",
            json={
                "status": "completo",
                "prioridad": "Alta",
                "altura_total_in": 42.0,
            },
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["status"] == "completo"

    def test_patch_nonexistent_solicitud(self, client):
        """Patching a non-existent solicitud returns 404."""
        response = client.patch("/api/solicitudes/99999", json={"status": "completo"})
        assert response.status_code == 404


class TestPhotoUpload:
    """POST /api/upload-foto — photo upload endpoint."""

    def test_upload_jpeg(self, client):
        """Uploading a valid JPEG returns foto_url."""
        fake_image = io.BytesIO(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
        response = client.post(
            "/api/upload-foto",
            files={"foto": ("test.jpg", fake_image, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "foto_url" in data
        assert data["foto_url"].startswith("/uploads/")

    def test_upload_png(self, client):
        """Uploading a valid PNG returns foto_url."""
        fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        response = client.post(
            "/api/upload-foto",
            files={"foto": ("test.png", fake_image, "image/png")},
        )
        assert response.status_code == 200
        assert "foto_url" in response.json()

    def test_upload_invalid_file_type(self, client):
        """Uploading a PDF is rejected."""
        fake_file = io.BytesIO(b"%PDF-1.4" + b"\x00" * 100)
        response = client.post(
            "/api/upload-foto",
            files={"foto": ("test.pdf", fake_file, "application/pdf")},
        )
        assert response.status_code == 400

    def test_upload_empty_file(self, client):
        """Uploading an empty file is rejected by request validation."""
        response = client.post(
            "/api/upload-foto",
            files={"foto": ("", b"", "image/jpeg")},
        )
        assert response.status_code == 422
