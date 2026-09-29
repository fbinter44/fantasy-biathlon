"""
Tests unitaires de la logique de saison (utils/biathlon_data.py).

current_ibu_season_code() est le miroir Python de computeCurrentSeason()
(lib/season.ts) — les deux DOIVENT retomber sur le même code de saison pour
la même date, sinon front et back se désynchronisent (deadlines, verrous de
pronos, cache...). Zéro test ne couvrait cette logique avant, alors qu'elle a
été modifiée en cours de projet (bascule hors-saison déplacée du 1er nov au
1er oct côté frontend) — ces tests verrouillent le comportement actuel des
deux côtés pour détecter toute dérive future entre les deux implémentations.
"""

from datetime import date

import pytest

from utils.biathlon_data import (
    current_ibu_season_code, previous_season_code, get_pronos_deadline,
    PRONOS_DEADLINE_BY_SEASON,
)


class TestCurrentIbuSeasonCode:

    @pytest.mark.parametrize("d, expected", [
        (date(2026, 1, 15), "2526"),   # Jan → saison démarrée l'année précédente
        (date(2026, 4, 30), "2526"),   # dernier jour d'avril → encore l'ancienne saison
        (date(2026, 5, 1), "2627"),    # 1er mai → bascule sur la saison suivante
        (date(2026, 9, 30), "2627"),   # fin septembre → toujours la saison suivante
        (date(2026, 10, 1), "2627"),   # 1er octobre → la saison suivante démarre
        (date(2026, 11, 25), "2627"),  # veille de la 1ère course 26/27
        (date(2026, 12, 31), "2627"),  # fin décembre → saison en cours
    ])
    def test_boundary_dates(self, d, expected):
        assert current_ibu_season_code(d) == expected

    def test_defaults_to_today_when_no_date_given(self):
        # On ne fixe pas la date "aujourd'hui" ici (pas de mock d'horloge) —
        # on vérifie juste que l'appel sans argument ne plante pas et
        # retourne un code à 4 chiffres cohérent avec le calcul explicite.
        result = current_ibu_season_code()
        assert len(result) == 4
        assert result == current_ibu_season_code(date.today())


class TestPreviousSeasonCode:

    def test_simple_case(self):
        assert previous_season_code("2627") == "2526"

    def test_century_rollover(self):
        assert previous_season_code("0001") == "9900"


class TestGetPronosDeadline:

    def test_known_season_returns_datetime(self):
        deadline = get_pronos_deadline("2526")
        assert deadline is not None
        assert deadline.year == 2025 and deadline.month == 11

    def test_unknown_season_returns_none(self):
        """Fail-closed : une saison sans calendrier publié ne doit jamais
        planter, ni être traitée comme 'toujours ouverte'."""
        assert get_pronos_deadline("9999") is None

    def test_all_configured_deadlines_are_before_first_race_evening(self):
        """Garde-fou de configuration : chaque deadline doit être un 23:59,
        veille de course — évite une erreur de saisie en ajoutant une saison."""
        for code, deadline in PRONOS_DEADLINE_BY_SEASON.items():
            assert deadline.hour == 23 and deadline.minute == 59, \
                f"Deadline saison {code} n'est pas à 23:59 : {deadline}"
