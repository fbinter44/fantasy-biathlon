"""
Tests unitaires du cache générique du classement (backend/services/classement_cache.py).

Ce module est la source du vrai bug corrigé cette saison : le cache du
classement ne se rafraîchissait que sur "la liste des joueurs a changé" ou
"5h après la dernière course" — avant la 1ère course d'une saison, remplir
ou modifier ses pronos ne faisait bouger ni l'un ni l'autre, donc un joueur
voyait un classement figé sur "vide" après avoir rempli ses pronos.
pronos_fingerprint_seed() corrige ça en rendant l'empreinte sensible au
contenu des pronos — zéro test ne couvrait ce module avant.
"""

import os
import pickle
from datetime import datetime, timedelta, timezone

from backend.services.classement_cache import pronos_fingerprint_seed, _fingerprint, get_or_compute


# ─── pronos_fingerprint_seed ───────────────────────────────────────────────────

class TestPronosFingerprintSeed:

    def _record(self, **overrides) -> dict:
        base = {
            "user_id": "u1", "top5_h": "A,B,C,D,E", "top5_f": "F,G,H,I,J",
            "globe_sprint_h": "A", "globe_sprint_f": "F",
            "globe_pursuit_h": "B", "globe_pursuit_f": "G",
            "globe_individual_h": "C", "globe_individual_f": "H",
            "globe_mass_start_h": "D", "globe_mass_start_f": "I",
        }
        base.update(overrides)
        return base

    def test_empty_records_returns_empty_seed(self):
        assert pronos_fingerprint_seed([]) == []

    def test_one_seed_string_per_record(self):
        seed = pronos_fingerprint_seed([self._record(), self._record(user_id="u2")])
        assert len(seed) == 2

    def test_identical_content_same_seed_string(self):
        s1 = pronos_fingerprint_seed([self._record(user_id="u1")])
        s2 = pronos_fingerprint_seed([self._record(user_id="u1")])
        assert s1 == s2

    def test_changing_top5_changes_seed(self):
        """Le coeur du bug corrigé : remplir/modifier ses pronos doit changer
        l'empreinte, même quand personne n'a rejoint/quitté et qu'aucune
        course n'a encore eu lieu."""
        before = pronos_fingerprint_seed([self._record(top5_h="")])
        after = pronos_fingerprint_seed([self._record(top5_h="A,B,C,D,E")])
        assert before != after

    def test_changing_globe_pick_changes_seed(self):
        before = pronos_fingerprint_seed([self._record(globe_sprint_h="A")])
        after = pronos_fingerprint_seed([self._record(globe_sprint_h="Z")])
        assert before != after

    def test_missing_fields_default_to_empty_string_not_crash(self):
        seed = pronos_fingerprint_seed([{"user_id": "u1"}])
        assert len(seed) == 1
        assert isinstance(seed[0], str)


# ─── _fingerprint ───────────────────────────────────────────────────────────────

class TestFingerprint:

    def test_deterministic_for_same_input(self):
        assert _fingerprint(["a", "b"]) == _fingerprint(["a", "b"])

    def test_order_independent(self):
        """La liste de seeds combine souvent des IDs joueurs (ordre DB) et
        des signatures de contenu — l'empreinte ne doit pas dépendre de leur
        ordre, sinon un simple retri déclencherait un recalcul inutile."""
        assert _fingerprint(["a", "b", "c"]) == _fingerprint(["c", "a", "b"])

    def test_different_content_different_fingerprint(self):
        assert _fingerprint(["a", "b"]) != _fingerprint(["a", "c"])

    def test_empty_seed_is_stable(self):
        assert _fingerprint([]) == _fingerprint([])


# ─── get_or_compute ─────────────────────────────────────────────────────────────

class FakeClient:
    """Double minimal d'IBUClient : seul get_last_race_end() est utilisé par
    get_or_compute() pour décider si le cache est encore frais."""

    def __init__(self, last_race_end=None):
        self._last_race_end = last_race_end

    def get_last_race_end(self):
        return self._last_race_end


class TestGetOrCompute:

    def test_cache_miss_calls_compute_fn(self, tmp_path):
        calls = []
        def compute():
            calls.append(1)
            return "data-v1"

        result = get_or_compute("test.pkl", FakeClient(), ["seed1"], compute, cache_dir=str(tmp_path))
        assert result == "data-v1"
        assert len(calls) == 1

    def test_cache_hit_with_same_seed_skips_compute_fn(self, tmp_path):
        """Pas de course jouée (last_race_end=None) + même seed → le cache
        déjà écrit doit être réutilisé sans rappeler compute_fn."""
        calls = []
        def compute():
            calls.append(1)
            return f"data-v{len(calls)}"

        client = FakeClient(last_race_end=None)
        get_or_compute("test.pkl", client, ["seed1"], compute, cache_dir=str(tmp_path))
        result = get_or_compute("test.pkl", client, ["seed1"], compute, cache_dir=str(tmp_path))

        assert result == "data-v1"  # toujours la 1ère valeur, pas recalculée
        assert len(calls) == 1

    def test_changed_seed_forces_recompute(self, tmp_path):
        """C'est exactement le scénario du bug corrigé : le seed change
        (contenu des pronos modifié) → recalcul, même sans nouvelle course."""
        calls = []
        def compute():
            calls.append(1)
            return f"data-v{len(calls)}"

        client = FakeClient(last_race_end=None)
        get_or_compute("test.pkl", client, ["seed1"], compute, cache_dir=str(tmp_path))
        result = get_or_compute("test.pkl", client, ["seed2"], compute, cache_dir=str(tmp_path))

        assert result == "data-v2"
        assert len(calls) == 2

    def test_stale_cache_after_race_forces_recompute(self, tmp_path):
        """Même empreinte, mais should_refresh_after_race() dit que le cache
        est périmé (course terminée il y a >5h, jamais rafraîchi depuis) →
        recalcul malgré l'empreinte identique. On pré-écrit directement un
        cache "vieux" plutôt que d'enchaîner deux appels (qui écriraient un
        cache_timestamp "maintenant", trop frais pour retomber dans la
        fenêtre de retry de should_refresh_after_race)."""
        seed = ["seed1"]
        stale_path = os.path.join(str(tmp_path), "test.pkl")
        old_race_end = datetime.now(timezone.utc) - timedelta(hours=10)
        with open(stale_path, "wb") as f:
            pickle.dump({
                "data": "data-stale",
                "timestamp": old_race_end - timedelta(hours=1),  # caché avant la course
                "fingerprint": _fingerprint(seed),
            }, f)

        calls = []
        def compute():
            calls.append(1)
            return "data-fresh"

        client = FakeClient(last_race_end=old_race_end)
        result = get_or_compute("test.pkl", client, seed, compute, cache_dir=str(tmp_path))

        assert result == "data-fresh"
        assert len(calls) == 1

    def test_different_cache_files_are_independent(self, tmp_path):
        """Deux clés de cache différentes (ex. deux ligues) ne doivent pas
        se marcher dessus."""
        result_a = get_or_compute("a.pkl", FakeClient(), ["seed"], lambda: "A", cache_dir=str(tmp_path))
        result_b = get_or_compute("b.pkl", FakeClient(), ["seed"], lambda: "B", cache_dir=str(tmp_path))
        assert result_a == "A"
        assert result_b == "B"
