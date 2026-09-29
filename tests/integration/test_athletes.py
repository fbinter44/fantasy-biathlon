"""
Tests d'intégration de la route /athletes.

Données statiques (JSON) — pas de mock Google Sheets nécessaire.
"""


class TestAthletes:

    def test_list_all_returns_200(self, client):
        resp = client.get("/athletes")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_contains_expected_fields(self, client):
        resp = client.get("/athletes")
        data = resp.json()
        if data:
            athlete = data[0]
            assert "ibu_id" in athlete
            assert "family_name" in athlete
            assert "given_name" in athlete
            assert "nation" in athlete
            assert "flag" in athlete
            assert "gender" in athlete
            assert "label" in athlete

    def test_filter_men_only(self, client):
        resp = client.get("/athletes?gender=M")
        assert resp.status_code == 200
        data = resp.json()
        assert all(a["gender"] == "M" for a in data)

    def test_filter_women_only(self, client):
        resp = client.get("/athletes?gender=W")
        assert resp.status_code == 200
        data = resp.json()
        assert all(a["gender"] == "W" for a in data)

    def test_invalid_gender_returns_422(self, client):
        resp = client.get("/athletes?gender=X")
        assert resp.status_code == 422

    def test_men_and_women_together_make_full_list(self, client):
        all_athletes  = client.get("/athletes").json()
        men_athletes  = client.get("/athletes?gender=M").json()
        women_athletes = client.get("/athletes?gender=W").json()
        assert len(men_athletes) + len(women_athletes) == len(all_athletes)

    def test_active_athletes_come_before_inactive(self, client):
        """Priorité 3 niveaux (top standings > participants saison > reste) —
        partition stricte, jamais un actif après un inactif dans la liste."""
        data = client.get("/athletes").json()
        statuses = [a["is_active"] for a in data]
        first_inactive = next((i for i, s in enumerate(statuses) if not s), len(statuses))
        assert all(statuses[:first_inactive])
        assert not any(statuses[first_inactive:])

    def test_inactive_athletes_sorted_alphabetically(self, client):
        """Le groupe des inactifs (un seul niveau de priorité) est alphabétique."""
        data = client.get("/athletes").json()
        inactive_names = [a["family_name"] for a in data if not a["is_active"]]
        assert inactive_names == sorted(inactive_names)

    def test_get_athlete_by_id_returns_200(self, client):
        all_athletes = client.get("/athletes").json()
        if not all_athletes:
            return
        first_id = all_athletes[0]["ibu_id"]
        resp = client.get(f"/athletes/{first_id}")
        assert resp.status_code == 200
        assert resp.json()["ibu_id"] == first_id

    def test_get_unknown_athlete_returns_404(self, client):
        resp = client.get("/athletes/UNKNOWN_ID_XYZ_123")
        assert resp.status_code == 404
