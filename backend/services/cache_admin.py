"""
Opérations d'administration sur le cache disque (core/ibu + classement calculé).

On se contente de supprimer les fichiers concernés : le prochain appel normal
reconstruit les données via la logique de cache déjà en place (pas de refetch
actif ici, pour rester simple et éviter une requête qui enchaînerait des
dizaines d'appels IBU).
"""

import os

from utils.cache_helpers import (
    CACHE_VENUES_DIR,
    CACHE_RESULTS_DIR,
    CACHE_STANDINGS_DIR,
    CACHE_CLASSEMENT_DIR,
    CACHE_ATHLETES_DIR,
)

SCOPE_DIRS = {
    "venues": CACHE_VENUES_DIR,
    "results": CACHE_RESULTS_DIR,
    "standings": CACHE_STANDINGS_DIR,
    "classement": CACHE_CLASSEMENT_DIR,
    "athletes": CACHE_ATHLETES_DIR,
}

# Scopes dont les fichiers sont nommés "..._{saison}.pkl" (classement calculé,
# score détaillé, priorité des athlètes) plutôt que "BT{saison}SWRLCP...".
_SUFFIX_SCOPES = {"classement", "athletes"}


def _matches_season(filename: str, season: str, scope: str) -> bool:
    if scope in _SUFFIX_SCOPES:
        # global_{saison}.pkl, league_{id}_{saison}.pkl, evolution_{saison}.pkl,
        # score_{user_id}_{saison}.pkl, priority_ibu_ids_{saison}.pkl
        return filename.endswith(f"_{season}.pkl")
    # BT{saison}SWRLCP...
    return filename.startswith(f"BT{season}")


def clear_cache(season: str, scope: str = "all") -> dict[str, int]:
    """Supprime les fichiers de cache d'une saison donnée. Retourne le nombre
    de fichiers supprimés par catégorie."""
    if scope != "all" and scope not in SCOPE_DIRS:
        raise ValueError(f"Scope inconnu : {scope!r}. Valeurs possibles : all, {', '.join(SCOPE_DIRS)}.")

    scopes = list(SCOPE_DIRS) if scope == "all" else [scope]

    deleted: dict[str, int] = {}
    for sc in scopes:
        directory = SCOPE_DIRS[sc]
        count = 0
        if os.path.isdir(directory):
            for filename in os.listdir(directory):
                if _matches_season(filename, season, sc):
                    os.remove(os.path.join(directory, filename))
                    count += 1
        deleted[sc] = count
    return deleted
