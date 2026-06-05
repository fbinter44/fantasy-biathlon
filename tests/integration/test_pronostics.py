"""
Tests d'intégration des routes /pronostics.
"""


class TestGetAllPronostics:

    def test_returns_200(self, client):
        resp = client.get("/pronostics")
        assert resp.status_code == 200

    def test_returns_list(self, client):
        resp = client.get("/pronostics")
        assert isinstance(resp.json(), list)

    def test_contains_expected_fields(self, client):
        data = client.get("/pronostics").json()
        if data:
            p = data[0]
            assert "user_id" in p
            assert "username" in p
            assert "top5_h" in p
            assert "top5_f" in p
            assert "globes" in p

    def test_top5_has_5_positions(self, client):
        data = client.get("/pronostics").json()
        if data:
            top5 = data[0]["top5_h"]
            assert all(k in top5 for k in ["p1", "p2", "p3", "p4", "p5"])


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

    def test_existing_user_returns_200(self, client):
        resp = client.get("/pronostics/test001")
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "test001"

    def test_unknown_user_returns_404(self, client):
        resp = client.get("/pronostics/unknown_user_xyz")
        assert resp.status_code == 404


class TestUpdateMyPronostics:

    def test_requires_auth(self, client):
        resp = client.put("/pronostics/me", json={})
        assert resp.status_code in (401, 403)

    def test_update_top5_h(self, client, auth_headers):
        resp = client.put("/pronostics/me", headers=auth_headers, json={
            "top5_h": {"p1": "X1", "p2": "X2", "p3": "X3", "p4": "X4", "p5": "X5"},
        })
        assert resp.status_code == 200

    def test_partial_update_only_top5_f(self, client, auth_headers):
        """Peut mettre à jour un seul champ sans toucher aux autres."""
        resp = client.put("/pronostics/me", headers=auth_headers, json={
            "top5_f": {"p1": "F1", "p2": "F2", "p3": "F3", "p4": "F4", "p5": "F5"},
        })
        assert resp.status_code == 200

    def test_update_globes(self, client, auth_headers):
        resp = client.put("/pronostics/me", headers=auth_headers, json={
            "globes": {
                "sprint_h": "Z1", "sprint_f": "Z2",
                "pursuit_h": "Z3", "pursuit_f": "Z4",
                "individual_h": "Z5", "individual_f": "Z6",
                "mass_start_h": "Z7", "mass_start_f": "Z8",
            }
        })
        assert resp.status_code == 200
