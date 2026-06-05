"""
Configuration des tests d'intégration.

On mocke api.services.db directement — chaque router importe ses fonctions
depuis ce module, donc un seul point de patch suffit.
"""

import pytest
import bcrypt
from contextlib import ExitStack
from unittest.mock import patch
from fastapi.testclient import TestClient

from api.main import app
from api.config import Settings


# ─── Données de test ─────────────────────────────────────────────────────────

def _hash(pwd: str) -> str:
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

TEST_USERS = [
    {
        "user_id":       "test001",
        "username":      "testuser",
        "email":         "test@example.com",
        "password_hash": _hash("password123"),
        "reset_code":    "",
    }
]
TEST_PRONOSTICS = [
    {
        "user_id":             "test001",
        "top5_h":              "A,B,C,D,E",
        "top5_f":              "F,G,H,I,J",
        "globe_sprint_h":      "A", "globe_sprint_f":      "F",
        "globe_pursuit_h":     "B", "globe_pursuit_f":     "G",
        "globe_individual_h":  "C", "globe_individual_f":  "H",
        "globe_mass_start_h":  "D", "globe_mass_start_f":  "I",
    }
]
TEST_LEAGUES: list[dict] = []

FAKE_SETTINGS = Settings(
    database_url="postgresql://fake/test",
    jwt_secret="test-secret-for-testing-only",
    brevo_api_key="fake",
    brevo_sender="test@example.com",
    ibu_season_code="2526",
)


# ─── Fonctions de mock db ─────────────────────────────────────────────────────

def _get_user_by_identifier(identifier: str, *a, **kw):
    identifier = identifier.lower()
    return next(
        (u for u in TEST_USERS if u["username"] == identifier or u["email"] == identifier),
        None,
    )

def _get_user_by_id(user_id: str, *a, **kw):
    return next((u for u in TEST_USERS if u["user_id"] == user_id), None)

def _get_all_users(*a, **kw):
    return list(TEST_USERS)

def _username_exists(username: str, *a, **kw):
    return any(u["username"] == username.lower() for u in TEST_USERS)

def _email_exists(email: str, *a, **kw):
    return any(u["email"] == email.lower() for u in TEST_USERS)

def _create_user(user_id, username, email, password_hash, *a, **kw):
    TEST_USERS.append({"user_id": user_id, "username": username,
                        "email": email, "password_hash": password_hash, "reset_code": ""})

def _update_user_field(user_id, field, value, *a, **kw):
    for u in TEST_USERS:
        if u["user_id"] == user_id:
            u[field] = value

def _get_all_pronostics(*a, **kw):
    return list(TEST_PRONOSTICS)

def _get_pronostics_by_user(user_id: str, *a, **kw):
    return next((p for p in TEST_PRONOSTICS if p["user_id"] == user_id), None)

def _upsert_pronostics(user_id, *a, **kw):
    pass

def _get_all_leagues(*a, **kw):
    return list(TEST_LEAGUES)

def _get_league_by_id(league_id: str, *a, **kw):
    return next((lg for lg in TEST_LEAGUES if lg["league_id"] == league_id), None)

def _get_league_by_invite_code(code: str, *a, **kw):
    return next((lg for lg in TEST_LEAGUES if lg.get("invite_code") == code), None)

def _create_league(league_id, name, owner, members, invite_code, *a, **kw):
    TEST_LEAGUES.append({"league_id": league_id, "league_name": name,
                          "owner": owner, "members": members, "invite_code": invite_code})

def _update_league_members(league_id, members_str, *a, **kw):
    for lg in TEST_LEAGUES:
        if lg["league_id"] == league_id:
            lg["members"] = members_str

def _delete_league_by_id(league_id, *a, **kw):
    TEST_LEAGUES[:] = [lg for lg in TEST_LEAGUES if lg["league_id"] != league_id]


# ─── Fixture principale ───────────────────────────────────────────────────────

_DB_MOCKS = {
    "get_all_users":             _get_all_users,
    "get_user_by_id":            _get_user_by_id,
    "get_user_by_identifier":    _get_user_by_identifier,
    "username_exists":           _username_exists,
    "email_exists":              _email_exists,
    "create_user":               _create_user,
    "update_user_field":         _update_user_field,
    "get_all_pronostics":        _get_all_pronostics,
    "get_pronostics_by_user":    _get_pronostics_by_user,
    "upsert_pronostics":         _upsert_pronostics,
    "get_all_leagues":           _get_all_leagues,
    "get_league_by_id":          _get_league_by_id,
    "get_league_by_invite_code": _get_league_by_invite_code,
    "create_league":             _create_league,
    "update_league_members":     _update_league_members,
    "delete_league_by_id":       _delete_league_by_id,
}

_ROUTERS = [
    "api.routers.auth",
    "api.routers.pronostics",
    "api.routers.leagues",
    "api.routers.classement",
]


@pytest.fixture
def client():
    with ExitStack() as stack:
        for router in _ROUTERS:
            for fn_name, fn in _DB_MOCKS.items():
                try:
                    stack.enter_context(patch(f"{router}.{fn_name}", side_effect=fn))
                except AttributeError:
                    pass  # ce router n'importe pas cette fonction

        stack.enter_context(patch("api.routers.auth.send_reset_email", return_value=True))
        stack.enter_context(patch("api.config.get_settings", return_value=FAKE_SETTINGS))

        with TestClient(app) as c:
            yield c


@pytest.fixture
def auth_token(client):
    resp = client.post("/auth/login", json={
        "identifier": "testuser",
        "password":   "password123",
    })
    assert resp.status_code == 200, resp.json()
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
