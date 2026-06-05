"""
Configuration partagée pour les tests d'intégration.

Problème classique de mock Python :
  Chaque router fait `from api.services.sheets import read_all`.
  Patcher `api.services.sheets.read_all` ne suffit pas — chaque router
  garde sa propre référence locale. Il faut patcher dans chaque module.
"""

import pytest
import bcrypt
from contextlib import ExitStack
from unittest.mock import patch, MagicMock
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
    sheet_id="fake",
    gcp_service_account_json='{"type":"service_account"}',
    jwt_secret="test-secret-for-testing-only",
    brevo_api_key="fake",
    brevo_sender="test@example.com",
    ibu_season_code="2526",
)


# ─── Mock feuilles ────────────────────────────────────────────────────────────

def fake_read_all(name: str, *args, **kwargs) -> list[dict]:
    if name == "Users":      return list(TEST_USERS)
    if name == "Pronostics": return list(TEST_PRONOSTICS)
    if name == "Leagues":    return list(TEST_LEAGUES)
    return []


def fake_get_sheet(name: str, *args, **kwargs) -> MagicMock:
    """Retourne un faux objet gspread Worksheet."""
    sheet = MagicMock()
    sheet.get_all_records.return_value = fake_read_all(name)
    sheet.col_values.return_value = [r.get("user_id", "") for r in fake_read_all(name)]
    return sheet


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    with ExitStack() as stack:
        # auth      : read_all, get_sheet, append_row, update_cell
        stack.enter_context(patch("api.routers.auth.read_all",    side_effect=fake_read_all))
        stack.enter_context(patch("api.routers.auth.get_sheet",   side_effect=fake_get_sheet))
        stack.enter_context(patch("api.routers.auth.append_row",  return_value=None))
        stack.enter_context(patch("api.routers.auth.update_cell", return_value=None))
        stack.enter_context(patch("api.routers.auth.send_reset_email", return_value=True))

        # pronostics : read_all, get_sheet, update_cell
        stack.enter_context(patch("api.routers.pronostics.read_all",    side_effect=fake_read_all))
        stack.enter_context(patch("api.routers.pronostics.get_sheet",   side_effect=fake_get_sheet))
        stack.enter_context(patch("api.routers.pronostics.update_cell", return_value=None))

        # leagues   : read_all, get_sheet, append_row, update_cell, delete_row
        stack.enter_context(patch("api.routers.leagues.read_all",    side_effect=fake_read_all))
        stack.enter_context(patch("api.routers.leagues.get_sheet",   side_effect=fake_get_sheet))
        stack.enter_context(patch("api.routers.leagues.append_row",  return_value=None))
        stack.enter_context(patch("api.routers.leagues.update_cell", return_value=None))
        stack.enter_context(patch("api.routers.leagues.delete_row",  return_value=None))

        # classement : read_all seulement
        stack.enter_context(patch("api.routers.classement.read_all", side_effect=fake_read_all))

        # settings globaux
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
