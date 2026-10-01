"""
Règles de confidentialité partagées entre /pronostics et /score : un joueur
ne doit voir les pronostics (ou le détail de score, qui les expose) d'un
autre que si (a) la deadline saison est passée, et (b) ils partagent au
moins un ski club. Ses propres pronostics/score restent toujours visibles.

Utilisé par backend/routers/pronostics.py et backend/routers/score.py.
"""

from datetime import datetime

from backend.config import Settings
from backend.services.db import get_all_leagues
from utils.biathlon_data import get_pronos_deadline
from utils.sheets import parse_members


def league_mates(user_id: str, settings: Settings) -> set[str]:
    """IDs des joueurs partageant au moins une ligue avec user_id (lui inclus)."""
    mates = {user_id}
    for lg in get_all_leagues(settings):
        members = parse_members(lg.get("members", ""))
        if user_id in members:
            mates.update(members)
    return mates


def deadline_passed(season_code: str) -> bool:
    """Fail-closed : si la deadline n'est pas encore configurée pour la saison,
    on considère qu'elle n'est pas passée (donc les pronos des autres restent masqués)."""
    deadline = get_pronos_deadline(season_code)
    return deadline is not None and datetime.now() > deadline
