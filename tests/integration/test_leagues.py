"""
Tests d'intégration des routes /leagues.
"""

import pytest
from unittest.mock import patch


class TestGetMyLeagues:

    def test_requires_auth(self, client):
        resp = client.get("/leagues")
        assert resp.status_code in (401, 403)

    def test_returns_empty_list_when_no_leagues(self, client, auth_headers):
        resp = client.get("/leagues", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []


class TestCreateLeague:

    def test_requires_auth(self, client):
        resp = client.post("/leagues", json={"name": "Test Club"})
        assert resp.status_code in (401, 403)

    def test_create_league_returns_201(self, client, auth_headers):
        resp = client.post("/leagues", headers=auth_headers, json={"name": "Les Chamois"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Les Chamois"
        assert "league_id" in data
        assert "invite_code" in data
        assert len(data["invite_code"]) == 6

    def test_created_league_has_creator_as_owner(self, client, auth_headers):
        resp = client.post("/leagues", headers=auth_headers, json={"name": "Mon Club"})
        assert resp.json()["owner_id"] == "test001"

    def test_created_league_creator_is_member(self, client, auth_headers):
        resp = client.post("/leagues", headers=auth_headers, json={"name": "Mon Club"})
        members = [m["user_id"] for m in resp.json()["members"]]
        assert "test001" in members

    def test_missing_name_returns_422(self, client, auth_headers):
        resp = client.post("/leagues", headers=auth_headers, json={})
        assert resp.status_code == 422


class TestGetLeague:

    def test_unknown_league_returns_404(self, client):
        resp = client.get("/leagues/unknown_id_xyz")
        assert resp.status_code == 404


class TestJoinLeague:

    def test_requires_auth(self, client):
        resp = client.post("/leagues/join", json={"invite_code": "ABC123"})
        assert resp.status_code in (401, 403)

    def test_invalid_code_returns_404(self, client, auth_headers):
        resp = client.post("/leagues/join", headers=auth_headers,
                           json={"invite_code": "XXXXXX"})
        assert resp.status_code == 404

    def test_valid_code_joins_league(self, client, auth_headers):
        from tests.integration.conftest import TEST_LEAGUES
        TEST_LEAGUES.append({
            "league_id":   "league01",
            "league_name": "Club Invité",
            "owner":       "other_user",
            "members":     "other_user",
            "invite_code": "JOINME",
        })
        try:
            resp = client.post("/leagues/join", headers=auth_headers,
                               json={"invite_code": "JOINME"})
            assert resp.status_code == 200
            members = [m["user_id"] for m in resp.json()["members"]]
            assert "test001" in members
        finally:
            TEST_LEAGUES.clear()

    def test_already_member_returns_400(self, client, auth_headers):
        from tests.integration.conftest import TEST_LEAGUES
        TEST_LEAGUES.append({
            "league_id":   "league02",
            "league_name": "Déjà membre",
            "owner":       "test001",
            "members":     "test001",
            "invite_code": "ALREADY",
        })
        try:
            resp = client.post("/leagues/join", headers=auth_headers,
                               json={"invite_code": "ALREADY"})
            assert resp.status_code == 400
        finally:
            TEST_LEAGUES.clear()


class TestDeleteLeague:

    def test_requires_auth(self, client):
        resp = client.delete("/leagues/league01")
        assert resp.status_code in (401, 403)

    def test_non_owner_cannot_delete(self, client, auth_headers):
        from tests.integration.conftest import TEST_LEAGUES
        TEST_LEAGUES.append({
            "league_id":   "league03",
            "league_name": "Pas mon club",
            "owner":       "other_user",
            "members":     "other_user,test001",
            "invite_code": "NOTMINE",
        })
        try:
            resp = client.delete("/leagues/league03", headers=auth_headers)
            assert resp.status_code == 403
        finally:
            TEST_LEAGUES.clear()

    def test_owner_can_delete(self, client, auth_headers):
        from tests.integration.conftest import TEST_LEAGUES
        TEST_LEAGUES.append({
            "league_id":   "league04",
            "league_name": "Mon club",
            "owner":       "test001",
            "members":     "test001",
            "invite_code": "MYCLUB",
        })
        try:
            resp = client.delete("/leagues/league04", headers=auth_headers)
            assert resp.status_code == 204
        finally:
            TEST_LEAGUES.clear()

    def test_unknown_league_returns_404(self, client, auth_headers):
        resp = client.delete("/leagues/unknown_xyz", headers=auth_headers)
        assert resp.status_code == 404


class TestLeaveLeague:

    def test_owner_cannot_leave(self, client, auth_headers):
        from tests.integration.conftest import TEST_LEAGUES
        TEST_LEAGUES.append({
            "league_id":   "league05",
            "league_name": "Je suis owner",
            "owner":       "test001",
            "members":     "test001",
            "invite_code": "OWNER1",
        })
        try:
            resp = client.delete("/leagues/league05/leave", headers=auth_headers)
            assert resp.status_code == 400
        finally:
            TEST_LEAGUES.clear()

    def test_member_can_leave(self, client, auth_headers):
        from tests.integration.conftest import TEST_LEAGUES
        TEST_LEAGUES.append({
            "league_id":   "league06",
            "league_name": "Je suis membre",
            "owner":       "other_user",
            "members":     "other_user,test001",
            "invite_code": "LEAVE1",
        })
        try:
            resp = client.delete("/leagues/league06/leave", headers=auth_headers)
            assert resp.status_code == 204
        finally:
            TEST_LEAGUES.clear()
