"""
Tests unitaires des helpers purs de backend/routers/classement.py.

Régression : les 3 routes /classement* (et /score/{user_id}) mettent en cache
leur résultat avec une empreinte construite à partir des IDs des joueurs
concernés — mais PAS de leur username, qui est pourtant renvoyé dans la
réponse (PlayerPoints.username / ScoreBreakdown.username). Changer de pseudo
ne touche ni aux pronos ni aux résultats IBU, donc rien d'autre ne force un
recalcul : le classement restait figé sur l'ancien pseudo jusqu'à ce qu'un
autre évènement invalide le cache par ailleurs. _id_username_seed() corrige
ça en incluant le username dans l'empreinte.
"""

from backend.routers.classement import _id_username_seed


def test_seed_includes_username_not_just_id():
    users = [{"user_id": "u1", "username": "florian"}]
    seed = _id_username_seed(users, ["u1"])
    assert seed == ["u1:florian"]


def test_username_change_changes_the_seed():
    users_before = [{"user_id": "u1", "username": "florian"}]
    users_after = [{"user_id": "u1", "username": "flo_renamed"}]
    seed_before = _id_username_seed(users_before, ["u1"])
    seed_after = _id_username_seed(users_after, ["u1"])
    assert seed_before != seed_after


def test_unrelated_username_change_does_not_affect_seed():
    """Un changement de pseudo d'un joueur HORS de la liste `ids` concernée
    (ex. un autre ski club) ne doit pas faire bouger l'empreinte."""
    users = [
        {"user_id": "u1", "username": "florian"},
        {"user_id": "u2", "username": "caroline"},
    ]
    seed_before = _id_username_seed(users, ["u1"])
    users[1]["username"] = "caro_renamed"
    seed_after = _id_username_seed(users, ["u1"])
    assert seed_before == seed_after


def test_filters_to_requested_ids_only():
    users = [
        {"user_id": "u1", "username": "florian"},
        {"user_id": "u2", "username": "caroline"},
        {"user_id": "u3", "username": "toto"},
    ]
    seed = _id_username_seed(users, ["u1", "u3"])
    assert seed == ["u1:florian", "u3:toto"]
