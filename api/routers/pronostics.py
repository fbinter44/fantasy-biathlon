"""
Routes pronostics joueurs.

GET  /pronostics              → tous les pronostics (public après deadline)
GET  /pronostics/me           → mes pronostics (authentifié)
PUT  /pronostics/me           → modifier mes pronostics (authentifié, avant deadline)
GET  /pronostics/{user_id}    → pronostics d'un joueur spécifique
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status

from api.config import Settings, get_settings
from api.dependencies import get_current_user
from api.models.pronostics import PronosticsResponse, PronosticsUpdateRequest, Top5, GlobeWinners
from api.services.sheets import read_all, get_sheet, update_cell
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


def _username_map(settings: Settings) -> dict:
    users = read_all("Users", settings)
    return {u["user_id"]: u["username"] for u in users}


@router.get("", response_model=list[PronosticsResponse])
def list_all_pronostics(settings: Settings = Depends(get_settings)):
    pronos = read_all("Pronostics", settings)
    umap = _username_map(settings)
    return [_row_to_response(r, umap) for r in pronos]


@router.get("/me", response_model=PronosticsResponse)
def my_pronostics(
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    pronos = read_all("Pronostics", settings)
    umap = _username_map(settings)
    for row in pronos:
        if row["user_id"] == current_user:
            return _row_to_response(row, umap)
    raise HTTPException(status_code=404, detail="Aucun pronostic trouvé pour cet utilisateur.")


@router.put("/me", response_model=PronosticsResponse)
def update_my_pronostics(
    body: PronosticsUpdateRequest,
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    if datetime.now() > PRONOS_DEADLINE:
        raise HTTPException(status_code=403, detail="La deadline des pronostics est passée.")

    sheet = get_sheet("Pronostics", settings)
    all_rows = sheet.get_all_records()
    user_ids = [r["user_id"] for r in all_rows]

    if current_user not in user_ids:
        # Créer la ligne si elle n'existe pas encore
        empty_row = [current_user, "", "", "", "", "", "", "", "", "", ""]
        sheet.append_row(empty_row)
        from api.services.sheets import _invalidate
        _invalidate("Pronostics")
        all_rows = sheet.get_all_records()
        user_ids = [r["user_id"] for r in all_rows]

    row_index = user_ids.index(current_user) + 2  # +2 : header + 0-based

    # Colonnes Pronostics sheet (à adapter selon la structure réelle)
    col_map = {
        "top5_h": 2, "top5_f": 3,
        "globe_sprint_h": 4, "globe_sprint_f": 5,
        "globe_pursuit_h": 6, "globe_pursuit_f": 7,
        "globe_individual_h": 8, "globe_individual_f": 9,
        "globe_mass_start_h": 10, "globe_mass_start_f": 11,
    }

    if body.top5_h:
        t5h = ",".join([body.top5_h.p1, body.top5_h.p2, body.top5_h.p3,
                        body.top5_h.p4, body.top5_h.p5])
        update_cell("Pronostics", row_index, col_map["top5_h"], t5h, settings)

    if body.top5_f:
        t5f = ",".join([body.top5_f.p1, body.top5_f.p2, body.top5_f.p3,
                        body.top5_f.p4, body.top5_f.p5])
        update_cell("Pronostics", row_index, col_map["top5_f"], t5f, settings)

    if body.globes:
        g = body.globes
        for field, col in [
            ("sprint_h", "globe_sprint_h"), ("sprint_f", "globe_sprint_f"),
            ("pursuit_h", "globe_pursuit_h"), ("pursuit_f", "globe_pursuit_f"),
            ("individual_h", "globe_individual_h"), ("individual_f", "globe_individual_f"),
            ("mass_start_h", "globe_mass_start_h"), ("mass_start_f", "globe_mass_start_f"),
        ]:
            val = getattr(g, field, "")
            update_cell("Pronostics", row_index, col_map[col], val, settings)

    return my_pronostics(current_user=current_user, settings=settings)


@router.get("/{user_id}", response_model=PronosticsResponse)
def get_user_pronostics(user_id: str, settings: Settings = Depends(get_settings)):
    pronos = read_all("Pronostics", settings)
    umap = _username_map(settings)
    for row in pronos:
        if row["user_id"] == user_id:
            return _row_to_response(row, umap)
    raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
