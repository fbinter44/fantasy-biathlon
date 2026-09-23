"""
Cache du classement fantasy calculé (backend/routers/classement.py).

Le calcul (lecture DB des pronos + reconstruction pandas + scoring) est
coûteux et identique tant que :
  1) les résultats IBU sous-jacents n'ont pas bougé — même règle de
     fraîcheur que le cache des standings IBU (5h après la dernière course,
     voir utils/cache_helpers.should_refresh_after_race) ;
  2) la liste des joueurs concernés n'a pas changé — sinon une inscription
     ou l'ajout d'un membre à une ligue resterait invisible jusqu'à la
     prochaine course.
"""

import os
import pickle
from datetime import datetime, timezone
from typing import Callable, TypeVar

from core.ibu.client import IBUClient
from utils.cache_helpers import CACHE_CLASSEMENT_DIR, cache_path, should_refresh_after_race, save_pickle_atomic

T = TypeVar("T")


def _fingerprint(user_ids: list[str]) -> str:
    """Empreinte bon marché de la liste des joueurs concernés."""
    return str(hash(tuple(sorted(user_ids))))


def get_or_compute(cache_file: str, client: IBUClient, user_ids: list[str], compute_fn: Callable[[], T]) -> T:
    """Retourne le résultat en cache s'il est encore frais, sinon recalcule via
    compute_fn() et met à jour le cache."""
    path = cache_path(CACHE_CLASSEMENT_DIR, cache_file)
    fingerprint = _fingerprint(user_ids)

    cached = None
    if os.path.exists(path):
        with open(path, "rb") as f:
            cached = pickle.load(f)

    if cached is not None and cached.get("fingerprint") == fingerprint:
        last_race_end = client.get_last_race_end()
        if not should_refresh_after_race(last_race_end, cached.get("timestamp")):
            return cached["data"]

    data = compute_fn()
    save_pickle_atomic(path, {"data": data, "timestamp": datetime.now(timezone.utc), "fingerprint": fingerprint})
    return data
