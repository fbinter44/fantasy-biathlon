"""
Tests d'intégration des routes d'authentification.
"""

from unittest.mock import patch

import pytest

from tests.integration.conftest import TEST_USERS


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


class TestEmailVerification:

    @staticmethod
    def _register(client, username):
        resp = client.post("/auth/register", json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 201
        return next(u for u in TEST_USERS if u["username"] == username)

    def test_register_sends_activation_email_with_link(self, client):
        with patch("backend.routers.auth.send_verification_email", return_value=True) as send:
            user = self._register(client, "verifmail")
        assert user["email_verified"] is False
        to_email, username, link, _ = send.call_args.args
        assert to_email == "verifmail@example.com"
        assert username == "verifmail"
        assert link.endswith(f"/verify-email?token={user['verify_token']}")

    def test_login_before_activation_returns_403(self, client):
        self._register(client, "notyet")
        resp = client.post("/auth/login", json={"identifier": "notyet", "password": "secret123"})
        assert resp.status_code == 403

    def test_login_unverified_wrong_password_returns_401(self, client):
        self._register(client, "notyet2")
        resp = client.post("/auth/login", json={"identifier": "notyet2", "password": "wrong"})
        assert resp.status_code == 401

    def test_verify_email_activates_and_returns_token(self, client):
        user = self._register(client, "toverify")
        resp = client.post("/auth/verify-email", json={"token": user["verify_token"]})
        assert resp.status_code == 200
        assert "access_token" in resp.json()
        assert user["email_verified"] is True
        login = client.post("/auth/login", json={"identifier": "toverify", "password": "secret123"})
        assert login.status_code == 200

    def test_verify_email_token_is_single_use(self, client):
        user = self._register(client, "onceonly")
        token = user["verify_token"]
        assert client.post("/auth/verify-email", json={"token": token}).status_code == 200
        assert client.post("/auth/verify-email", json={"token": token}).status_code == 400

    def test_verify_email_invalid_token_returns_400(self, client):
        resp = client.post("/auth/verify-email", json={"token": "nope"})
        assert resp.status_code == 400

    def test_verify_email_expired_token_returns_400(self, client):
        user = self._register(client, "expired1")
        user["verify_expires"] = 0
        resp = client.post("/auth/verify-email", json={"token": user["verify_token"]})
        assert resp.status_code == 400
        assert user["email_verified"] is False

    def test_register_fails_and_rolls_back_when_email_not_sent(self, client):
        with patch("backend.routers.auth.send_verification_email", return_value=False):
            resp = client.post("/auth/register", json={
                "username": "nomail", "email": "nomail@example.com", "password": "secret123",
            })
        assert resp.status_code == 500
        assert not any(u["username"] == "nomail" for u in TEST_USERS)

    def test_register_reuses_expired_unverified_username(self, client):
        user = self._register(client, "squatter")
        user["verify_expires"] = 0
        resp = client.post("/auth/register", json={
            "username": "squatter", "email": "realowner@example.com", "password": "secret123",
        })
        assert resp.status_code == 201

    def test_resend_verification_renews_token(self, client):
        user = self._register(client, "resendme")
        old_token = user["verify_token"]
        with patch("backend.routers.auth.send_verification_email", return_value=True) as send:
            resp = client.post("/auth/resend-verification", json={"identifier": "resendme"})
        assert resp.status_code == 200
        assert send.called
        assert user["verify_token"] != old_token

    def test_resend_verification_unknown_or_verified_is_silent(self, client):
        with patch("backend.routers.auth.send_verification_email", return_value=True) as send:
            assert client.post("/auth/resend-verification", json={"identifier": "nobody"}).status_code == 200
            assert client.post("/auth/resend-verification", json={"identifier": "testuser"}).status_code == 200
        assert not send.called


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
