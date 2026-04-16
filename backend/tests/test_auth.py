"""
Tests for the auth (login) endpoint.

Covers:
- C2: Login upsert (no duplicate capturistas)
- Validation: name must be >= 2 characters
"""
import sqlite3
import pytest


class TestLogin:
    """POST /api/login — upsert login for capturistas."""

    def test_create_new_capturista(self, client):
        """New name creates a new capturista."""
        response = client.post("/api/login", json={"nombre": "Ana García"})
        assert response.status_code == 200
        data = response.json()
        assert data["capturista_id"] is not None
        assert data["nombre"] == "Ana García"

    def test_login_same_name_returns_same_id(self, client):
        """C2: Re-login with same name returns same capturista_id (no duplicates)."""
        r1 = client.post("/api/login", json={"nombre": "Carlos López"})
        assert r1.status_code == 200
        id_first = r1.json()["capturista_id"]

        r2 = client.post("/api/login", json={"nombre": "Carlos López"})
        assert r2.status_code == 200
        id_second = r2.json()["capturista_id"]

        assert id_first == id_second, "Same name should return same capturista_id"

    def test_different_names_different_ids(self, client):
        """Different names get different IDs."""
        r1 = client.post("/api/login", json={"nombre": "Persona Uno"})
        r2 = client.post("/api/login", json={"nombre": "Persona Dos"})
        assert r1.json()["capturista_id"] != r2.json()["capturista_id"]

    def test_name_too_short_rejected(self, client):
        """Name < 2 characters is rejected by Pydantic validation."""
        response = client.post("/api/login", json={"nombre": "A"})
        assert response.status_code == 422

    def test_name_stripped_before_validation(self, client):
        """Name with leading/trailing whitespace is stripped."""
        r = client.post("/api/login", json={"nombre": "  Juan  "})
        assert r.status_code == 200
        assert r.json()["nombre"] == "Juan"

    def test_no_duplicate_rows_in_db(self, client, _session_db):
        """Verify the database has no duplicate nombres after multiple logins."""
        client.post("/api/login", json={"nombre": "Repetido"})
        client.post("/api/login", json={"nombre": "Repetido"})
        client.post("/api/login", json={"nombre": "Repetido"})

        conn = sqlite3.connect(_session_db)
        rows = conn.execute(
            "SELECT id, nombre FROM capturistas WHERE nombre = 'Repetido'"
        ).fetchall()
        conn.close()
        assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"