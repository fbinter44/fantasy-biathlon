"""
Routes ligues.

GET    /leagues            → mes ligues (authentifié)
POST   /leagues            → créer une ligue (authentifié)
POST   /leagues/join       → rejoindre via invite_code (authentifié)
DELETE /leagues/{id}       → supprimer (owner uniquement)
GET    /leagues/{id}       → détails d'une ligue
DELETE /leagues/{id}/leave → quitter une ligue
"""

import uuid
import random
import string

from fastapi import APIRouter, Depends, HTTPException, status

from api.config import Settings, get_settings
from api.dependencies import get_current_user
from api.models.leagues import LeagueCreate, LeagueJoin, LeagueResponse, LeagueListItem, LeagueMember
from api.services.sheets import read_all, append_row, get_sheet, update_cell
from utils.sheets import parse_members

router = APIRouter(prefix="/leagues", tags=["leagues"])


# ---------------------------------------------------------
# helpers
# ---------------------------------------------------------

def _unique_league_id(existing_ids: set) -> str:
    while True:
        lid = str(uuid.uuid4())[:8]
        if lid not in existing_ids:
            return lid


def _unique_invite_code(existing_codes: set, length: int = 6) -> str:
    chars = string.ascii_uppercase + string.digits
    while True:
        code = "".join(random.choice(chars) for _ in range(length))
        if code not in existing_codes:
            return code


def _members_to_model(member_ids: list[str], users: list[dict]) -> list[LeagueMember]:
    umap = {u["user_id"]: u["username"] for u in users}
    return [LeagueMember(user_id=uid, username=umap.get(uid, uid)) for uid in member_ids]


def _league_to_response(lg: dict, users: list[dict]) -> LeagueResponse:
    members = parse_members(lg.get("members", ""))
    return LeagueResponse(
        league_id=lg["league_id"],
        name=lg["league_name"],
        owner_id=lg["owner"],
        invite_code=lg.get("invite_code", ""),
        members=_members_to_model(members, users),
    )


# ---------------------------------------------------------
# routes
# ---------------------------------------------------------

@router.get("", response_model=list[LeagueListItem])
def my_leagues(
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    leagues = read_all("Leagues", settings)
    result = []
    for lg in leagues:
        members = parse_members(lg.get("members", ""))
        if current_user in members:
            result.append(LeagueListItem(
                league_id=lg["league_id"],
                name=lg["league_name"],
                member_count=len(members),
                is_owner=(lg["owner"] == current_user),
            ))
    return result


@router.post("", response_model=LeagueResponse, status_code=status.HTTP_201_CREATED)
def create_league(
    body: LeagueCreate,
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    leagues = read_all("Leagues", settings)
    users = read_all("Users", settings)

    existing_ids = {lg["league_id"] for lg in leagues}
    existing_codes = {lg.get("invite_code", "") for lg in leagues}

    league_id = _unique_league_id(existing_ids)
    invite_code = _unique_invite_code(existing_codes)

    append_row("Leagues", [league_id, body.name, current_user, current_user, invite_code], settings)

    new_league = {
        "league_id": league_id,
        "league_name": body.name,
        "owner": current_user,
        "members": current_user,
        "invite_code": invite_code,
    }
    return _league_to_response(new_league, users)


@router.post("/join", response_model=LeagueResponse)
def join_league(
    body: LeagueJoin,
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    sheet = get_sheet("Leagues", settings)
    leagues = sheet.get_all_records()
    users = read_all("Users", settings)

    for i, lg in enumerate(leagues, start=2):
        if lg.get("invite_code") == body.invite_code:
            members = parse_members(lg.get("members", ""))
            if current_user in members:
                raise HTTPException(status_code=400, detail="Tu es déjà membre de cette ligue.")
            members.append(current_user)
            update_cell("Leagues", i, 4, ",".join(members), settings)
            lg["members"] = ",".join(members)
            return _league_to_response(lg, users)

    raise HTTPException(status_code=404, detail="Code d'invitation invalide.")


@router.get("/{league_id}", response_model=LeagueResponse)
def get_league(league_id: str, settings: Settings = Depends(get_settings)):
    leagues = read_all("Leagues", settings)
    users = read_all("Users", settings)
    lg = next((l for l in leagues if l["league_id"] == league_id), None)
    if not lg:
        raise HTTPException(status_code=404, detail="Ligue introuvable.")
    return _league_to_response(lg, users)


@router.delete("/{league_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_league(
    league_id: str,
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    sheet = get_sheet("Leagues", settings)
    leagues = sheet.get_all_records()

    for i, lg in enumerate(leagues, start=2):
        if lg["league_id"] == league_id:
            if lg["owner"] != current_user:
                raise HTTPException(status_code=403, detail="Seul le propriétaire peut supprimer la ligue.")
            sheet.delete_rows(i)
            return

    raise HTTPException(status_code=404, detail="Ligue introuvable.")


@router.delete("/{league_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_league(
    league_id: str,
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    sheet = get_sheet("Leagues", settings)
    leagues = sheet.get_all_records()

    for i, lg in enumerate(leagues, start=2):
        if lg["league_id"] == league_id:
            members = parse_members(lg.get("members", ""))
            if current_user not in members:
                raise HTTPException(status_code=400, detail="Tu n'es pas membre de cette ligue.")
            if lg["owner"] == current_user:
                raise HTTPException(status_code=400, detail="Le propriétaire ne peut pas quitter sa ligue. Supprimez-la.")
            members.remove(current_user)
            update_cell("Leagues", i, 4, ",".join(members), settings)
            return

    raise HTTPException(status_code=404, detail="Ligue introuvable.")
