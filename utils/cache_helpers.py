import logging
import os
import pickle
import tempfile
import time
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


CACHE_VENUES_DIR = "cache/cache_venues"
CACHE_RESULTS_DIR = "cache/cache_results"
CACHE_STANDINGS_DIR = "cache/cache_standings"
CACHE_CLASSEMENT_DIR = "cache/cache_classement"
CACHE_ATHLETES_DIR = "cache/cache_athletes"


def cache_path(dir, file):
    os.makedirs(dir, exist_ok=True)
    return os.path.join(dir, file)


def save_pickle_atomic(path: str, data, *, max_attempts: int = 5) -> None:
    """
    Écrit un fichier pickle de façon atomique : on écrit dans un fichier
    temporaire puis on le renomme sur la cible (os.replace, atomique sur
    Windows comme sur POSIX). Évite qu'une lecture concurrente tombe sur un
    fichier à moitié écrit si deux requêtes rafraîchissent le même cache en
    même temps.

    Sous Windows, ce renommage peut échouer par intermittence (PermissionError)
    si un autre thread a le fichier cible ouvert en lecture au même instant
    (chaque requête FastAPI tourne dans son propre thread) — on retente
    quelques fois avant d'abandonner. Le cache est un confort de performance,
    pas une donnée critique : en cas d'échec persistant, on log et on
    abandonne sans faire planter l'appelant (la donnée fraîchement calculée
    reste utilisable pour la requête en cours, seule la mise en cache échoue).
    """
    directory = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".tmp-", suffix=".pkl")
    try:
        with os.fdopen(fd, "wb") as f:
            pickle.dump(data, f)

        for attempt in range(max_attempts):
            try:
                os.replace(tmp_path, path)
                return
            except PermissionError:
                if attempt == max_attempts - 1:
                    logger.warning("Écriture du cache abandonnée après %d tentatives : %s", max_attempts, path)
                    return
                time.sleep(0.05 * (attempt + 1))
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def should_refresh_after_race(
    reference_time,
    cache_timestamp,
    grace_hours: float = 5,
    retry_interval_hours: float = 0.5,
    retry_window_hours: float = 24,
) -> bool:
    """
    Règle de fraîcheur partagée par les caches dérivés des résultats IBU
    (standings, résultats de course, classement fantasy calculé). `reference_time`
    est soit l'heure de la dernière course terminée (cache saison), soit l'heure
    de départ d'une course précise (cache par course).

    - Pas de refresh avant `grace_hours` après `reference_time` (le temps que
      l'IBU publie les résultats officiels).
    - Passé ce délai, premier refresh si le cache est absent ou antérieur à
      `reference_time`.
    - Ensuite, nouvelles tentatives périodiques (toutes les `retry_interval_hours`)
      pendant une fenêtre de `retry_window_hours` après `reference_time` — pour
      absorber une publication tardive (jury, contrôle antidopage, retard
      technique) au lieu de se figer sur un résultat incomplet récupéré au
      tout premier essai.
    - Passé cette fenêtre, on considère les résultats définitifs et on arrête
      de retenter (jusqu'à la course suivante).
    """
    if reference_time is None:
        return False

    now = datetime.now(timezone.utc)
    if now < reference_time + timedelta(hours=grace_hours):
        return False

    if cache_timestamp is None:
        return True

    if cache_timestamp < reference_time:
        return True

    if now < reference_time + timedelta(hours=retry_window_hours):
        return now >= cache_timestamp + timedelta(hours=retry_interval_hours)

    return False


def should_refresh_calendar(venue_start, cache_timestamp, refresh_interval_hours: float = 24) -> bool:
    """
    Fraîcheur du calendrier d'une venue (liste de courses + horaires) — logique
    inverse de should_refresh_after_race : le risque de changement est **avant**
    l'événement (l'IBU peut ajuster un horaire), pas après.

    - Venue déjà passée → jamais de refresh (calendrier figé, comme une saison
      archivée).
    - Venue à venir → refresh périodique (toutes les `refresh_interval_hours`)
      pour absorber un ajustement d'horaire annoncé par l'IBU.
    """
    now = datetime.now(timezone.utc)

    if venue_start is not None and now >= venue_start:
        return False

    if cache_timestamp is None:
        return True

    return now >= cache_timestamp + timedelta(hours=refresh_interval_hours)
