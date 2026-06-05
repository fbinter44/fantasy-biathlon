"""
Tests d'intégration des routes d'authentification.
"""

import pytest


class TestLogin:

    def test_login_valid_credentials_returns_token(self, client):
        resp = client.post("/auth/login", json={
            "identifier": "testuser",
            "password": "password123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["username"] == "testuser"
        assert data["user_id"] == "test001"

    def test_login_by_email(self, client):
        resp = client.post("/auth/login", json={
            "identifier": "test@example.com",
            "password": "password123",
        })
        assert resp.status_code == 200

    def test_login_wrong_password_returns_401(self, client):
        resp = client.post("/auth/login", json={
            "identifier": "testuser",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_login_unknown_user_returns_401(self, client):
        resp = client.post("/auth/login", json={
            "identifier": "nobody",
            "password": "password123",
        })
        assert resp.status_code == 401

    def test_login_missing_fields_returns_422(self, client):
        resp = client.post("/auth/login", json={"identifier": "testuser"})
        assert resp.status_code == 422


class TestRegister:

    def test_register_new_user_returns_201(self, client):
        resp = client.post("/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert "user_id" in data
        assert "password_hash" not in data  # ne doit jamais être exposé

    def test_register_duplicate_username_returns_400(self, client):
        resp = client.post("/auth/register", json={
            "username": "testuser",  # déjà existant
            "email": "other@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 400

    def test_register_duplicate_email_returns_400(self, client):
        resp = client.post("/auth/register", json={
            "username": "otherusername",
            "email": "test@example.com",  # déjà existant
            "password": "secret123",
        })
        assert resp.status_code == 400

    def test_register_invalid_email_returns_422(self, client):
        resp = client.post("/auth/register", json={
            "username": "someone",
            "email": "not-an-email",
            "password": "secret123",
        })
        assert resp.status_code == 422


class TestProtectedRoute:

    def test_access_without_token_returns_403(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code in (401, 403)

    def test_access_with_valid_token_returns_200(self, client, auth_headers):
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["username"] == "testuser"

    def test_access_with_invalid_token_returns_401(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer fake.token.here"})
        assert resp.status_code == 401
