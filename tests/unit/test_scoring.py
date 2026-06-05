"""
Tests unitaires du moteur de scoring.
"""

import pandas as pd
import pytest

from core.scoring.compute_points import compute_regular_points, compute_globe_winner_bonus
from core.scoring.points_table import POINTS_TABLE


# ─── Fixtures ────────────────────────────────────────────────────────────────

def make_standings(id_rank_pairs: list[tuple[str, int]]) -> pd.DataFrame:
    """Crée un DataFrame de classement (rangs en string comme les vraies données IBU)."""
    return pd.DataFrame({
        "id":    [p[0] for p in id_rank_pairs],
        "rank":  [str(p[1]) for p in id_rank_pairs],  # string — comportement IBU réel
        "name":  [f"Athlete_{p[0]}" for p in id_rank_pairs],
        "points": [float(100 - p[1]) for p in id_rank_pairs],
    })


def make_top10(id_rank_pairs: list[tuple[str, int]]) -> pd.DataFrame:
    """Comme make_standings mais garantit que tous les rangs sont ≤ 10."""
    assert all(r <= 10 for _, r in id_rank_pairs), "top10 ne doit contenir que des rangs ≤ 10"
    return make_standings(id_rank_pairs)


class FakeGlobeWinners:
    def __init__(self, winner_men: str, winner_women: str):
        self.winner_men = winner_men
        self.winner_women = winner_women


# ─── Tests compute_regular_points ────────────────────────────────────────────

class TestComputeRegularPoints:

    def test_athlete_not_in_top10_earns_zero(self):
        standings = make_top10([("A", 1), ("B", 2)])
        pred = ["C", "D", "E", "F", "G"]
        total, bonus, details = compute_regular_points(pred, standings)
        assert total == 0
        assert bonus == 0

    def test_athlete_ranked_1st_earns_90_pts_no_bonus(self):
        """Athlète classé 1er mais prédit en 2ème position → 90 pts sans bonus."""
        standings = make_top10([("A", 1), ("B", 2), ("C", 3)])
        pred = ["X", "A", "X", "X", "X"]  # A prédit 2ème, mais classé 1er → pas de bonus
        total, bonus, _ = compute_regular_points(pred, standings)
        assert total == POINTS_TABLE[0]  # 90
        assert bonus == 0

    def test_exact_rank_bonus_50pts(self):
        """Athlète prédit à la place 2 ET classé 2ème → 75 + 50 = 125."""
        standings = make_top10([("A", 1), ("B", 2), ("C", 3)])
        pred = ["X", "B", "X", "X", "X"]
        total, bonus, _ = compute_regular_points(pred, standings)
        assert bonus == 50
        assert total == POINTS_TABLE[1] + 50  # 125

    def test_no_bonus_when_rank_differs(self):
        """Athlète prédit 1er mais classé 2ème → 75 pts, pas de bonus."""
        standings = make_top10([("A", 1), ("B", 2)])
        pred = ["B", "X", "X", "X", "X"]
        total, bonus, _ = compute_regular_points(pred, standings)
        assert bonus == 0
        assert total == POINTS_TABLE[1]  # 75

    def test_multiple_athletes_in_top10(self):
        """3 athlètes du top 5 dans le vrai top 10 → somme correcte."""
        standings = make_top10([
            ("A", 1), ("B", 2), ("C", 5), ("D", 8),
        ])
        pred = ["X", "A", "X", "C", "D"]  # aucun bonus car aucun rang exact
        total, bonus, details = compute_regular_points(pred, standings)
        assert details["A"] == POINTS_TABLE[0]   # 90
        assert details["C"] == POINTS_TABLE[4]   # 50
        assert details["D"] == POINTS_TABLE[7]   # 37
        assert total == 90 + 50 + 37
        assert bonus == 0

    def test_bonus_cumulates_for_multiple_exact_ranks(self):
        """Deux athlètes exactement au bon rang → 2 × 50 bonus."""
        standings = make_top10([("A", 1), ("B", 2), ("C", 3)])
        pred = ["A", "B", "X", "X", "X"]
        _, bonus, _ = compute_regular_points(pred, standings)
        assert bonus == 100

    def test_all_points_table_values_correct(self):
        """Vérifie le barème IBU pour chaque rang 1–10 (sans déclencher le bonus)."""
        for rank in range(1, 11):
            id_ = f"ATH{rank}"
            # On prédit l'athlète à une position différente de son rang réel
            pred_pos = (rank % 5) + 1  # décalage pour éviter le bonus
            standings = make_top10([(id_, rank)])
            pred = ["X"] * 5
            pred[pred_pos - 1] = id_
            total, bonus, _ = compute_regular_points(pred, standings)
            if pred_pos == rank:
                # Si par malchance les positions coïncident, on ignore le test de ce rang
                continue
            assert total == POINTS_TABLE[rank - 1], \
                f"Rang {rank} : attendu {POINTS_TABLE[rank - 1]}, obtenu {total}"
            assert bonus == 0

    def test_empty_standings_returns_zero(self):
        standings = pd.DataFrame({"id": [], "rank": [], "name": [], "points": []})
        total, bonus, _ = compute_regular_points(["A", "B", "C", "D", "E"], standings)
        assert total == 0
        assert bonus == 0


# ─── Tests compute_globe_winner_bonus ────────────────────────────────────────

class TestComputeGlobeWinnerBonus:

    def test_correct_men_winner_earns_50(self):
        men   = make_standings([("A", 1), ("B", 2)])
        women = make_standings([("C", 1)])
        pred  = FakeGlobeWinners(winner_men="A", winner_women="X")
        b_men, b_women = compute_globe_winner_bonus(pred, men, women)
        assert b_men == 50
        assert b_women == 0

    def test_correct_women_winner_earns_50(self):
        men   = make_standings([("A", 1)])
        women = make_standings([("C", 1), ("D", 2)])
        pred  = FakeGlobeWinners(winner_men="X", winner_women="C")
        b_men, b_women = compute_globe_winner_bonus(pred, men, women)
        assert b_men == 0
        assert b_women == 50

    def test_both_correct_earns_100(self):
        men   = make_standings([("A", 1)])
        women = make_standings([("C", 1)])
        pred  = FakeGlobeWinners(winner_men="A", winner_women="C")
        b_men, b_women = compute_globe_winner_bonus(pred, men, women)
        assert b_men == 50
        assert b_women == 50

    def test_both_wrong_earns_zero(self):
        men   = make_standings([("A", 1)])
        women = make_standings([("C", 1)])
        pred  = FakeGlobeWinners(winner_men="Z", winner_women="Z")
        b_men, b_women = compute_globe_winner_bonus(pred, men, women)
        assert b_men == 0
        assert b_women == 0

    def test_empty_standings_earns_zero(self):
        empty = pd.DataFrame({"id": [], "rank": [], "name": [], "points": []})
        pred  = FakeGlobeWinners(winner_men="A", winner_women="C")
        b_men, b_women = compute_globe_winner_bonus(pred, empty, empty)
        assert b_men == 0
        assert b_women == 0
