"""
Tests d'intégration des routes /pronostics.

GET /pronostics et GET /pronostics/{user_id} sont scopés vie privée : un
joueur ne voit que ses propres pronos, plus ceux de ses coéquipiers de ligue
une fois la deadline saison passée (voir backend/routers/pronostics.py). La
saison par défaut des tests (FAKE_SETTINGS.ibu_season_code = "2526") a une
deadline déjà passée (27 nov 2025), donc la visibilité "coéquipiers" y est
déjà débloquée sans avoir à mocker la date.
"""


class TestGetAllPronostics:

    def test_requires_auth(self, client):
        resp = client.get("/pronostics")
        assert resp.status_code in (401, 403)

    def test_authenticated_returns_200_list(self, client, auth_headers):
        resp = client.get("/pronostics", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_only_shows_self_when_no_shared_league(self, client, auth_headers):
        """Sans ligue en commun, seul son propre prono est visible — vie
        privée par défaut, même si d'autres joueurs ont des pronos en DB."""
        data = client.get("/pronostics", headers=auth_headers).json()
        assert all(p["user_id"] == "test001" for p in data)

    def test_contains_expected_fields(self, client, auth_headers):
        data = client.get("/pronostics", headers=auth_headers).json()
        assert data  # testuser voit toujours son propre prono
        p = data[0]
        assert "user_id" in p
        assert "username" in p
        assert "top5_h" in p
        assert "top5_f" in p
        assert "globes" in p

    def test_top5_has_5_positions(self, client, auth_headers):
        data = client.get("/pronostics", headers=auth_headers).json()
        top5 = data[0]["top5_h"]
        assert all(k in top5 for k in ["p1", "p2", "p3", "p4", "p5"])

    def test_league_mate_becomes_visible_after_deadline(self, client, auth_headers):
        """Un coéquipier de ligue devient visible (deadline saison passée),
        un non-coéquipier reste invisible même s'il a des pronos en DB."""
        from tests.integration.conftest import TEST_LEAGUES, TEST_PRONOSTICS
        TEST_LEAGUES.append({
            "league_id":   "league_privacy",
            "league_name": "Club Privacy",
            "owner":       "test001",
            "members":     "test001,mate001",
            "invite_code": "PRIVACY",
        })
        TEST_PRONOSTICS.append({
            "user_id": "mate001",
            "top5_h": "A,B,C,D,E", "top5_f": "F,G,H,I,J",
            "globe_sprint_h": "A", "globe_sprint_f": "F",
            "globe_pursuit_h": "B", "globe_pursuit_f": "G",
            "globe_individual_h": "C", "globe_individual_f": "H",
            "globe_mass_start_h": "D", "globe_mass_start_f": "I",
        })
        try:
            data = client.get("/pronostics", headers=auth_headers).json()
            visible_ids = {p["user_id"] for p in data}
            assert "mate001" in visible_ids
        finally:
            TEST_LEAGUES.clear()
            TEST_PRONOSTICS.pop()


class TestGetMyPronostics:

    def test_requires_auth(self, client):
        resp = client.get("/pronostics/me")
        assert resp.status_code in (401, 403)

    def test_returns_my_pronostics(self, client, auth_headers):
        resp = client.get("/pronostics/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "test001"
        assert data["username"] == "testuser"

    def test_top5_h_correct(self, client, auth_headers):
        resp = client.get("/pronostics/me", headers=auth_headers)
        top5 = resp.json()["top5_h"]
        assert top5["p1"] == "A"
        assert top5["p2"] == "B"
        assert top5["p5"] == "E"

    def test_globes_correct(self, client, auth_headers):
        resp = client.get("/pronostics/me", headers=auth_headers)
        globes = resp.json()["globes"]
        assert globes["sprint_h"] == "A"
        assert globes["sprint_f"] == "F"


class TestGetUserPronostics:

    def test_requires_auth(self, client):
        resp = client.get("/pronostics/test001")
        assert resp.status_code in (401, 403)

    def test_own_pronostics_returns_200(self, client, auth_headers):
        resp = client.get("/pronostics/test001", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "test001"

    def test_unrelated_user_returns_403_not_404(self, client, auth_headers):
        """Pas de fuite d'info : qu'il existe ou non, un joueur avec qui on
        ne partage aucune ligue renvoie 403 — évite l'énumération d'IDs."""
        resp = client.get("/pronostics/unknown_user_xyz", headers=auth_headers)
        assert resp.status_code == 403

    def test_league_mate_returns_404_when_no_pronos(self, client, auth_headers):
        """Coéquipier légitime (deadline passée) mais sans pronos en DB → 404,
        pas 403 : la permission est accordée, c'est juste que ça n'existe pas."""
        from tests.integration.conftest import TEST_LEAGUES
        TEST_LEAGUES.append({
            "league_id":   "league_404",
            "league_name": "Club 404",
            "owner":       "test001",
            "members":     "test001,mate_no_pronos",
            "invite_code": "NOPRONO",
        })
        try:
            resp = client.get("/pronostics/mate_no_pronos", headers=auth_headers)
            assert resp.status_code == 404
        finally:
            TEST_LEAGUES.clear()


class TestUpdateMyPronostics:
    """La saison par défaut des tests (2526) a une deadline déjà passée
    (27 nov 2025) — volontaire pour tester le verrou (voir plus bas). Les
    tests du "chemin heureux" passent explicitement `season=2627`, dont la
    deadline (25 nov 2026) n'est pas encore atteinte."""

    def test_requires_auth(self, client):
        resp = client.put("/pronostics/me", json={})
        assert resp.status_code in (401, 403)

    def test_update_top5_h(self, client, auth_headers):
        resp = client.put("/pronostics/me?season=2627", headers=auth_headers, json={
            "top5_h": {"p1": "X1", "p2": "X2", "p3": "X3", "p4": "X4", "p5": "X5"},
        })
        assert resp.status_code == 200

    def test_partial_update_only_top5_f(self, client, auth_headers):
        """Peut mettre à jour un seul champ sans toucher aux autres."""
        resp = client.put("/pronostics/me?season=2627", headers=auth_headers, json={
            "top5_f": {"p1": "F1", "p2": "F2", "p3": "F3", "p4": "F4", "p5": "F5"},
        })
        assert resp.status_code == 200

    def test_update_globes(self, client, auth_headers):
        resp = client.put("/pronostics/me?season=2627", headers=auth_headers, json={
            "globes": {
                "sprint_h": "Z1", "sprint_f": "Z2",
                "pursuit_h": "Z3", "pursuit_f": "Z4",
                "individual_h": "Z5", "individual_f": "Z6",
                "mass_start_h": "Z7", "mass_start_f": "Z8",
            }
        })
        assert resp.status_code == 200

    def test_update_after_deadline_returns_403(self, client, auth_headers):
        """Saison par défaut (2526) : deadline déjà passée → verrou actif."""
        resp = client.put("/pronostics/me", headers=auth_headers, json={
            "top5_h": {"p1": "X1", "p2": "X2", "p3": "X3", "p4": "X4", "p5": "X5"},
        })
        assert resp.status_code == 403

    def test_update_unknown_season_returns_403(self, client, auth_headers):
        """Saison sans deadline connue (calendrier pas encore publié) → fail
        closed, pas d'exception ni d'acceptation silencieuse."""
        resp = client.put("/pronostics/me?season=9999", headers=auth_headers, json={
            "top5_h": {"p1": "X1", "p2": "X2", "p3": "X3", "p4": "X4", "p5": "X5"},
        })
        assert resp.status_code == 403
