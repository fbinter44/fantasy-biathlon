"""
Routes pronostics joueurs.

GET  /pronostics              → tous les pronostics
GET  /pronostics/me           → mes pronostics (authentifié)
PUT  /pronostics/me           → modifier mes pronostics (authentifié, avant deadline)
GET  /pronostics/{user_id}    → pronostics d'un joueur
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from api.config import Settings, get_settings
from api.dependencies import get_current_user
from api.models.pronostics import PronosticsResponse, PronosticsUpdateRequest, Top5, GlobeWinners
from api.services.db import get_all_users, get_all_pronostics, get_pronostics_by_user, upsert_pronostics
from utils.biathlon_data import PRONOS_DEADLINE, split_top5

router = APIRouter(prefix="/pronostics", tags=["pronostics"])


def _row_to_response(row: dict, username_map: dict) -> PronosticsResponse:
    uid = row["user_id"]
    t5h = split_top5(row.get("top5_h", ""))
    t5f = split_top5(row.get("top5_f", ""))
    return PronosticsResponse(
        user_id=uid,
        username=username_map.get(uid, uid),
        top5_h=Top5(p1=t5h[0], p2=t5h[1], p3=t5h[2], p4=t5h[3], p5=t5h[4]),
        top5_f=Top5(p1=t5f[0], p2=t5f[1], p3=t5f[2], p4=t5f[3], p5=t5f[4]),
        globes=GlobeWinners(
            sprint_h=row.get("globe_sprint_h", ""),
            sprint_f=row.get("globe_sprint_f", ""),
            pursuit_h=row.get("globe_pursuit_h", ""),
            pursuit_f=row.get("globe_pursuit_f", ""),
            individual_h=row.get("globe_individual_h", ""),
            individual_f=row.get("globe_individual_f", ""),
            mass_start_h=row.get("globe_mass_start_h", ""),
            mass_start_f=row.get("globe_mass_start_f", ""),
        ),
    )


@router.get("", response_model=list[PronosticsResponse])
def list_all_pronostics(settings: Settings = Depends(get_settings)):
    pronos = get_all_pronostics(settings)
    users = get_all_users(settings)
    umap = {u["user_id"]: u["username"] for u in users}
    return [_row_to_response(r, umap) for r in pronos]


@router.get("/me", response_model=PronosticsResponse)
def my_pronostics(
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    row = get_pronostics_by_user(current_user, settings)
    if not row:
        raise HTTPException(status_code=404, detail="Aucun pronostic trouvé pour cet utilisateur.")
    users = get_all_users(settings)
    umap = {u["user_id"]: u["username"] for u in users}
    return _row_to_response(row, umap)


@router.put("/me", response_model=PronosticsResponse)
def update_my_pronostics(
    body: PronosticsUpdateRequest,
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    if datetime.now() > PRONOS_DEADLINE:
        raise HTTPException(status_code=403, detail="La deadline des pronostics est passée.")

    updates = {}

    if body.top5_h:
        updates["top5_h"] = ",".join([
            body.top5_h.p1, body.top5_h.p2, body.top5_h.p3,
            body.top5_h.p4, body.top5_h.p5,
        ])
    if body.top5_f:
        updates["top5_f"] = ",".join([
            body.top5_f.p1, body.top5_f.p2, body.top5_f.p3,
            body.top5_f.p4, body.top5_f.p5,
        ])
    if body.globes:
        g = body.globes
        updates["globe_sprint_h"]     = g.sprint_h     or ""
        updates["globe_sprint_f"]     = g.sprint_f     or ""
        updates["globe_pursuit_h"]    = g.pursuit_h    or ""
        updates["globe_pursuit_f"]    = g.pursuit_f    or ""
        updates["globe_individual_h"] = g.individual_h or ""
        updates["globe_individual_f"] = g.individual_f or ""
        updates["globe_mass_start_h"] = g.mass_start_h or ""
        updates["globe_mass_start_f"] = g.mass_start_f or ""

    upsert_pronostics(current_user, settings, **updates)
    return my_pronostics(current_user=current_user, settings=settings)


@router.get("/{user_id}", response_model=PronosticsResponse)
def get_user_pronostics(user_id: str, settings: Settings = Depends(get_settings)):
    row = get_pronostics_by_user(user_id, settings)
    if not row:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    users = get_all_users(settings)
    umap = {u["user_id"]: u["username"] for u in users}
    return _row_to_response(row, umap)
