"""
Tests unitaires du chargement et parsing des pronostics.
"""

import pandas as pd
import pytest

from core.pronostics.pronostics_loader import load_pronostics_from_records, parse_pronostics


# ─── Fixtures ────────────────────────────────────────────────────────────────

SAMPLE_RECORDS = [
    {
        "user_id": "user1",
        "top5_h": "A,B,C,D,E",
        "top5_f": "F,G,H,I,J",
        "globe_sprint_h": "A", "globe_sprint_f": "F",
        "globe_pursuit_h": "B", "globe_pursuit_f": "G",
        "globe_individual_h": "C", "globe_individual_f": "H",
        "globe_mass_start_h": "D", "globe_mass_start_f": "I",
    },
    {
        "user_id": "user2",
        "top5_h": "B,A,C,D,E",
        "top5_f": "G,F,H,I,J",
        "globe_sprint_h": "B", "globe_sprint_f": "G",
        "globe_pursuit_h": "A", "globe_pursuit_f": "F",
        "globe_individual_h": "D", "globe_individual_f": "I",
        "globe_mass_start_h": "E", "globe_mass_start_f": "J",
    },
]


# ─── load_pronostics_from_records ────────────────────────────────────────────

class TestLoadPronosticsFromRecords:

    def test_returns_dataframe(self):
        df = load_pronostics_from_records(SAMPLE_RECORDS)
        assert isinstance(df, pd.DataFrame)

    def test_correct_number_of_rows(self):
        df = load_pronostics_from_records(SAMPLE_RECORDS)
        assert len(df) == 2

    def test_has_expected_columns(self):
        df = load_pronostics_from_records(SAMPLE_RECORDS)
        assert "user_id" in df.columns
        assert "top5_h" in df.columns
        assert "top5_f" in df.columns

    def test_empty_records_raises(self):
        with pytest.raises(KeyError):
            load_pronostics_from_records([])

    def test_user_ids_preserved(self):
        df = load_pronostics_from_records(SAMPLE_RECORDS)
        assert set(df["user_id"].tolist()) == {"user1", "user2"}


# ─── parse_pronostics ────────────────────────────────────────────────────────

class TestParsePronostics:

    def setup_method(self):
        self.df = load_pronostics_from_records(SAMPLE_RECORDS)

    def test_returns_three_objects(self):
        result = parse_pronostics(self.df)
        assert len(result) == 3

    def test_top5_h_indexed_by_user_id(self):
        top5_h, _, _ = parse_pronostics(self.df)
        assert "user1" in top5_h.index
        assert "user2" in top5_h.index

    def test_top5_h_has_5_columns(self):
        top5_h, _, _ = parse_pronostics(self.df)
        assert top5_h.shape[1] == 5

    def test_top5_f_indexed_by_user_id(self):
        _, top5_f, _ = parse_pronostics(self.df)
        assert "user1" in top5_f.index

    def test_globes_contains_globe_columns(self):
        _, _, globes = parse_pronostics(self.df)
        assert "globe_sprint_h" in globes.columns
        assert "globe_sprint_f" in globes.columns

    def test_top5_h_first_athlete_correct(self):
        top5_h, _, _ = parse_pronostics(self.df)
        # user1 a mis A en premier
        assert top5_h.loc["user1", "p1"] == "A"

    def test_top5_h_user2_different_order(self):
        top5_h, _, _ = parse_pronostics(self.df)
        # user2 a mis B en premier
        assert top5_h.loc["user2", "p1"] == "B"

    def test_filter_by_subset_of_users(self):
        df_filtered = self.df[self.df["user_id"] == "user1"]
        top5_h, _, _ = parse_pronostics(df_filtered)
        assert len(top5_h) == 1
        assert "user1" in top5_h.index
        assert "user2" not in top5_h.index
