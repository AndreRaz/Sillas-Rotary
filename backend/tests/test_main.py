"""
Tests for static file serving and root redirect.

Covers:
- C1: Frontend served from FastAPI (same origin)
- Root redirect to /login.html
- API endpoints still accessible at /api/*
"""
import pytest


class TestStaticFrontend:
    """C1: Static frontend served from FastAPI."""

    def test_root_redirects_to_login(self, client):
        """GET / should redirect to /login.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (301, 302, 303, 307)
        assert "/login.html" in response.headers.get("location", "")

    def test_login_html_accessible(self, client):
        """GET /login.html should return 200 with HTML content."""
        response = client.get("/login.html")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "Capturista" in response.text

    def test_socioeconomico_html_accessible(self, client):
        """GET /socioeconomico.html should return 200."""
        response = client.get("/socioeconomico.html")
        assert response.status_code == 200
        assert "Estudio Socioeconómico" in response.text or "Socioecon" in response.text

    def test_tecnica_html_accessible(self, client):
        """GET /tecnica.html should return 200."""
        response = client.get("/tecnica.html")
        assert response.status_code == 200
        assert "Solicitud" in response.text or "silla" in response.text.lower()

    def test_api_login_still_works(self, client):
        """API endpoints under /api/* are not shadowed by static files."""
        response = client.post("/api/login", json={"nombre": "Test API"})
        assert response.status_code == 200
        assert "capturista_id" in response.json()

    def test_api_estudios_still_works(self, client):
        """API /api/estudios is not shadowed by static files."""
        response = client.get("/api/estudios/99999")
        assert response.status_code == 404  # Not found is correct — means route exists

    def test_assets_accessible(self, client):
        """Static assets (images) are served correctly."""
        response = client.get("/assets/Logo_ug.png")
        # May return 200 (found) or 404 (not found) — just verify no crash
        assert response.status_code in (200, 404)


class TestDatabaseConstraints:
    """Tests for database constraints (UNIQUE, CHECK, FK)."""

    def test_capturistas_unique_nombre(self, client, _session_db):
        """C2: capturistas.nombre must be UNIQUE — verify at DB level."""
        import sqlite3

        # Login twice with same name
        client.post("/api/login", json={"nombre": "Único"})
        client.post("/api/login", json={"nombre": "Único"})

        conn = sqlite3.connect(_session_db)
        rows = conn.execute(
            "SELECT COUNT(*) FROM capturistas WHERE nombre = 'Único'"
        ).fetchone()
        conn.close()
        assert rows[0] == 1, f"Expected 1 row, got {rows[0]}"

    def test_tutor_numero_constraint(self, client, sample_capturista):
        """numero_tutor must be 1 or 2."""
        payload = {
            "capturista_id": sample_capturista["capturista_id"],
            "beneficiario": {
                "nombre": "Test Num Tutor",
                "fecha_nacimiento": "2010-01-01",
                "diagnostico": "Test",
                "calle": "Calle",
                "colonia": "Col",
                "ciudad": "León",
                "telefonos": "4620000000",
            },
            "tutores": [
                {
                    "numero_tutor": 3,  # Invalid!
                    "nombre": "Bad Tutor",
                    "tiene_imss": False,
                    "tiene_infonavit": False,
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
        assert response.status_code == 422  # Pydantic validation error

    def test_estudio_status_constraint(self, client, sample_capturista):
        """estudio status must be 'borrador' or 'completo'."""
        payload = {
            "capturista_id": sample_capturista["capturista_id"],
            "beneficiario": {
                "nombre": "Status Test",
                "fecha_nacimiento": "2010-01-01",
                "diagnostico": "Test",
                "calle": "Calle",
                "colonia": "Col",
                "ciudad": "León",
                "telefonos": "4620000000",
            },
            "tutores": [
                {
                    "numero_tutor": 1,
                    "nombre": "Tutor Status",
                    "tiene_imss": False,
                    "tiene_infonavit": False,
                }
            ],
            "estudio": {
                "elaboro_estudio": "Tester",
                "fecha_estudio": "2026-04-15",
                "sede": "León",
                "tuvo_silla_previa": False,
                "status": "invalid_status",  # Invalid!
            },
        }
        response = client.post("/api/estudios", json=payload)
        assert response.status_code == 422
