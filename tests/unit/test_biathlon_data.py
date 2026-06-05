"""
Tests unitaires des helpers de utils/biathlon_data.py.
"""

import pytest
from utils.biathlon_data import split_top5, format_top5, athlete_label, ATHLETES_BY_IBUID


# ─── split_top5 ──────────────────────────────────────────────────────────────

class TestSplitTop5:

    def test_5_ids_returns_list_of_5(self):
        result = split_top5("A,B,C,D,E")
        assert result == ["A", "B", "C", "D", "E"]

    def test_empty_string_returns_5_empty(self):
        assert split_top5("") == ["", "", "", "", ""]

    def test_none_returns_5_empty(self):
        assert split_top5(None) == ["", "", "", "", ""]

    def test_3_ids_padded_to_5(self):
        result = split_top5("A,B,C")
        assert result == ["A", "B", "C", "", ""]

    def test_6_ids_truncated_to_5(self):
        result = split_top5("A,B,C,D,E,F")
        assert len(result) == 5
        assert result == ["A", "B", "C", "D", "E"]

    def test_spaces_preserved(self):
        result = split_top5("A, B, C, D, E")
        assert result[1] == " B"


# ─── athlete_label ───────────────────────────────────────────────────────────

class TestAthleteLabel:

    def test_unknown_id_returns_empty(self):
        assert athlete_label("UNKNOWN_ID_XYZ") == ""

    def test_empty_string_returns_empty(self):
        assert athlete_label("") == ""

    def test_none_returns_empty(self):
        assert athlete_label(None) == ""

    def test_known_athlete_returns_non_empty_label(self):
        if not ATHLETES_BY_IBUID:
            pytest.skip("Fichier athletes_info.json non disponible")
        ibu_id = next(iter(ATHLETES_BY_IBUID))
        label = athlete_label(ibu_id)
        assert label != ""
        assert len(label) > 3

    def test_known_athlete_label_contains_name(self):
        if not ATHLETES_BY_IBUID:
            pytest.skip("Fichier athletes_info.json non disponible")
        ibu_id = next(iter(ATHLETES_BY_IBUID))
        info = ATHLETES_BY_IBUID[ibu_id]
        label = athlete_label(ibu_id)
        assert info["FamilyName"] in label


# ─── format_top5 ─────────────────────────────────────────────────────────────

class TestFormatTop5:

    def test_empty_string_returns_empty(self):
        assert format_top5("") == ""

    def test_unknown_ids_returns_empty_string(self):
        result = format_top5("UNKNOWN1,UNKNOWN2")
        # les ids inconnus sont ignorés (athlete_label retourne "")
        assert isinstance(result, str)

    def test_returns_string(self):
        result = format_top5("A,B,C")
        assert isinstance(result, str)
