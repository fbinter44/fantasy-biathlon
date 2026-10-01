"""
Tests d'intégration de la route /score/{user_id}.

Régression : le détail de score (prédictions saison + course) n'appliquait
aucune règle de confidentialité, contrairement à /pronostics — n'importe quel
joueur authentifié pouvait consulter les pronos de n'importe qui, même avant
la deadline saison. Ces tests couvrent uniquement le garde-fou (403 rapide,
avant tout appel IBU/DB coûteux) : le chemin "accès autorisé" nécessiterait
de mocker IBUClient (standings réels), hors scope ici — voir aussi
tests/unit/test_classement_router_helpers.py pour la logique de fingerprint
du cache de cette même route.
"""


class TestScorePrivacy:

    def test_requires_auth(self, client):
        resp = client.get("/score/test001")
        assert resp.status_code in (401, 403)

    def test_unrelated_user_returns_403(self, client, auth_headers):
        """Pas de ligue en commun → 403, avant même de toucher à l'IBU/la DB."""
        resp = client.get("/score/unrelated_user_xyz", headers=auth_headers)
        assert resp.status_code == 403

    def test_league_mate_before_deadline_returns_403(self, client, auth_headers):
        """Coéquipier de ligue, mais deadline saison pas encore passée (saison
        sans calendrier connu) → toujours masqué, comme pour /pronostics."""
        from tests.integration.conftest import TEST_LEAGUES
        TEST_LEAGUES.append({
            "league_id":   "league_score_privacy",
            "league_name": "Club Score Privacy",
            "owner":       "test001",
            "members":     "test001,mate001",
            "invite_code": "SCOREPRIV",
        })
        try:
            resp = client.get("/score/mate001?season=9999", headers=auth_headers)
            assert resp.status_code == 403
        finally:
            TEST_LEAGUES.clear()
