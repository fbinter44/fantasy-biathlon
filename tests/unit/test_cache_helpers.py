"""
Tests unitaires des règles de fraîcheur du cache (utils/cache_helpers.py).

should_refresh_after_race() a été modifiée en cours de projet (passage d'un
"un seul essai à +5h puis figé pour toujours" à une fenêtre de retry de 24h)
pour absorber une publication tardive des résultats IBU — zéro test ne
couvrait cette logique avant, alors que c'est elle qui a permis de repérer et
corriger un vrai bug de cache cette saison (voir test_classement_cache.py).

Toutes les dates sont exprimées en delta autour de "maintenant" (pas de mock
d'horloge) — plus lisible et robuste dans le temps.
"""

from datetime import datetime, timedelta, timezone

from utils.cache_helpers import should_refresh_after_race, should_refresh_calendar

NOW = datetime.now(timezone.utc)


def ago(**kw) -> datetime:
    return NOW - timedelta(**kw)


def hence(**kw) -> datetime:
    return NOW + timedelta(**kw)


# ─── should_refresh_after_race ────────────────────────────────────────────────

class TestShouldRefreshAfterRace:

    def test_no_reference_time_never_refreshes(self):
        """Pas de course terminée (saison pas commencée) → jamais de refresh,
        c'est le vrai bug de cette saison si mal géré en amont (voir
        classement_cache.py, corrigé par le fingerprint sensible au contenu
        plutôt que de compter sur ce signal pour le pré-saison)."""
        assert should_refresh_after_race(None, ago(hours=100)) is False
        assert should_refresh_after_race(None, None) is False

    def test_within_grace_period_no_refresh(self):
        """Moins de 5h après la course → l'IBU n'a pas encore forcément publié."""
        reference = ago(hours=2)
        assert should_refresh_after_race(reference, None) is False

    def test_no_cache_yet_after_grace_period_refreshes(self):
        reference = ago(hours=6)
        assert should_refresh_after_race(reference, None) is True

    def test_stale_cache_older_than_reference_refreshes(self):
        reference = ago(hours=6)
        cache_timestamp = ago(hours=10)  # caché avant même la course
        assert should_refresh_after_race(reference, cache_timestamp) is True

    def test_fresh_cache_just_refreshed_no_refresh(self):
        reference = ago(hours=6)
        cache_timestamp = ago(minutes=1)  # vient d'être rafraîchi
        assert should_refresh_after_race(reference, cache_timestamp) is False

    def test_retry_window_retries_every_30min(self):
        """Dans la fenêtre de 24h après la course, on retente toutes les 30min
        si le cache commence à dater — absorbe une publication tardive."""
        reference = ago(hours=8)
        cache_timestamp = ago(hours=6, minutes=31)  # rafraîchi juste après la grâce, plus de 30min
        assert should_refresh_after_race(reference, cache_timestamp) is True

    def test_retry_window_too_soon_since_last_check_no_refresh(self):
        reference = ago(hours=8)
        cache_timestamp = ago(minutes=10)  # rafraîchi il y a moins de 30min
        assert should_refresh_after_race(reference, cache_timestamp) is False

    def test_after_retry_window_locked_forever(self):
        """Passé 24h après la course, on considère les résultats définitifs —
        plus de refresh même si le cache est ancien."""
        reference = ago(hours=30)
        cache_timestamp = ago(hours=29)  # vieux, mais fenêtre de retry dépassée
        assert should_refresh_after_race(reference, cache_timestamp) is False


# ─── should_refresh_calendar ───────────────────────────────────────────────────

class TestShouldRefreshCalendar:

    def test_past_venue_never_refreshes(self):
        """Venue déjà passée → calendrier figé, même sans cache du tout."""
        assert should_refresh_calendar(ago(days=1), None) is False
        assert should_refresh_calendar(ago(days=1), ago(days=10)) is False

    def test_upcoming_venue_no_cache_refreshes(self):
        assert should_refresh_calendar(hence(days=5), None) is True

    def test_upcoming_venue_fresh_cache_no_refresh(self):
        assert should_refresh_calendar(hence(days=5), ago(hours=1)) is False

    def test_upcoming_venue_stale_cache_refreshes(self):
        """Cache vieux de plus de 24h sur une venue à venir → on retente
        (l'IBU a pu ajuster l'horaire depuis)."""
        assert should_refresh_calendar(hence(days=5), ago(hours=25)) is True

    def test_no_venue_start_known_yet_treated_as_upcoming(self):
        """venue_start=None (calendrier jamais chargé) → traité comme à
        venir, pas comme passé — sinon on ne chargerait jamais rien."""
        assert should_refresh_calendar(None, None) is True
