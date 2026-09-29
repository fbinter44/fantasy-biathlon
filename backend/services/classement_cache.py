"""
Cache générique pour les calculs dérivés des données IBU + DB (classement
fantasy, score détaillé, priorité des athlètes dans les listes de pronos…).

Ces calculs sont coûteux (DB + pandas + parfois relecture de tous les
résultats de la saison) et identiques tant que :
  1) les résultats IBU sous-jacents n'ont pas bougé — même règle de
     fraîcheur que le cache des standings IBU (5h après la dernière course,
     voir utils/cache_helpers.should_refresh_after_race) ;
  2) la liste des "sujets" concernés (joueurs, ou tout autre identifiant
     passé en fingerprint) n'a pas changé.

Utilisé par backend/routers/classement.py, score.py et athletes.py.
"""

import os
import pickle
from datetime import datetime, timezone
from typing import Callable, TypeVar

from core.ibu.client import IBUClient
from utils.cache_helpers import CACHE_CLASSEMENT_DIR, cache_path, should_refresh_after_race, save_pickle_atomic

T = TypeVar("T")


_PRONOS_FIELDS = (
    "user_id", "top5_h", "top5_f",
    "globe_sprint_h", "globe_sprint_f",
    "globe_pursuit_h", "globe_pursuit_f",
    "globe_individual_h", "globe_individual_f",
    "globe_mass_start_h", "globe_mass_start_f",
)


def pronos_fingerprint_seed(records: list[dict]) -> list[str]:
    """
    Une chaîne de signature par ligne de pronostics saison, sensible au
    **contenu** (pas juste à l'identité du joueur) — à combiner avec la liste
    des joueurs concernés dans le fingerprint de get_or_compute.

    Nécessaire car should_refresh_after_race ne peut détecter un changement
    qu'après qu'une course ait eu lieu (via last_race_end) : avant la 1ère
    course de la saison, rien ne force sinon le cache à se rafraîchir quand
    quelqu'un modifie ses pronos.
    """
    return ["|".join(str(r.get(f, "")) for f in _PRONOS_FIELDS) for r in records]


def _fingerprint(seed: list[str]) -> str:
    """Empreinte bon marché d'une liste de chaînes (joueurs concernés, et/ou
    signatures de contenu type pronos_fingerprint_seed)."""
    return str(hash(tuple(sorted(seed))))


def get_or_compute(
    cache_file: str,
    client: IBUClient,
    fingerprint_seed: list[str],
    compute_fn: Callable[[], T],
    cache_dir: str = CACHE_CLASSEMENT_DIR,
) -> T:
    """Retourne le résultat en cache s'il est encore frais, sinon recalcule via
    compute_fn() et met à jour le cache. `cache_dir` par défaut sur le cache du
    classement fantasy ; passer un autre dossier (ex. CACHE_ATHLETES_DIR) pour
    d'autres calculs dérivés des mêmes règles de fraîcheur IBU."""
    path = cache_path(cache_dir, cache_file)
    fingerprint = _fingerprint(fingerprint_seed)

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
