"""
Routes d'administration — réservées aux comptes listés dans ADMIN_USERNAMES
(voir backend/config.py, backend/dependencies.require_admin). Pas exposées
aux joueurs.

POST /admin/cache/clear → vide le cache disque pour une saison (le prochain
                           appel normal reconstruit les données)
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.dependencies import require_admin
from backend.services.cache_admin import clear_cache

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/cache/clear")
def clear_cache_route(
    season: str = Query(..., description="Code de saison, ex. '2627'"),
    scope: str = Query("all", description="all | venues | results | standings | classement"),
    _admin: str = Depends(require_admin),
):
    try:
        deleted = clear_cache(season, scope)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"detail": "Cache vidé.", "season": season, "deleted": deleted}
