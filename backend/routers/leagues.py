"""
Routes ligues.

GET    /leagues            → mes ligues (authentifié)
POST   /leagues            → créer une ligue
POST   /leagues/join       → rejoindre via invite_code
GET    /leagues/{id}       → détails d'une ligue
DELETE /leagues/{id}       → supprimer (owner uniquement)
DELETE /leagues/{id}/leave → quitter
"""

import uuid
import random
import string

from fastapi import APIRouter, Depends, HTTPException, status

from backend.config import Settings, get_settings
from backend.dependencies import get_current_user
from backend.models.leagues import LeagueCreate, LeagueJoin, LeagueResponse, LeagueListItem, LeagueMember
from backend.services.db import (
    get_all_users, get_all_leagues,
    get_league_by_id, get_league_by_invite_code,
    create_league, update_league_members, delete_league_by_id,
)
from utils.sheets import parse_members

router = APIRouter(prefix="/leagues", tags=["leagues"])


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


@router.get("", response_model=list[LeagueListItem])
def my_leagues(
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    leagues = get_all_leagues(settings)
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
def create_league_route(
    body: LeagueCreate,
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    leagues = get_all_leagues(settings)
    users = get_all_users(settings)

    existing_ids = {lg["league_id"] for lg in leagues}
    existing_codes = {lg.get("invite_code", "") for lg in leagues}

    league_id = _unique_league_id(existing_ids)
    invite_code = _unique_invite_code(existing_codes)

    create_league(league_id, body.name, current_user, current_user, invite_code, settings)

    new_league = {
        "league_id":   league_id,
        "league_name": body.name,
        "owner":       current_user,
        "members":     current_user,
        "invite_code": invite_code,
    }
    return _league_to_response(new_league, users)


@router.post("/join", response_model=LeagueResponse)
def join_league(
    body: LeagueJoin,
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    lg = get_league_by_invite_code(body.invite_code, settings)
    if not lg:
        raise HTTPException(status_code=404, detail="Code d'invitation invalide.")

    members = parse_members(lg.get("members", ""))
    if current_user in members:
        raise HTTPException(status_code=400, detail="Tu es déjà membre de cette ligue.")

    members.append(current_user)
    update_league_members(lg["league_id"], ",".join(members), settings)

    users = get_all_users(settings)
    lg["members"] = ",".join(members)
    return _league_to_response(lg, users)


@router.get("/{league_id}", response_model=LeagueResponse)
def get_league(league_id: str, settings: Settings = Depends(get_settings)):
    lg = get_league_by_id(league_id, settings)
    if not lg:
        raise HTTPException(status_code=404, detail="Ligue introuvable.")
    users = get_all_users(settings)
    return _league_to_response(lg, users)


@router.delete("/{league_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_league(
    league_id: str,
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    lg = get_league_by_id(league_id, settings)
    if not lg:
        raise HTTPException(status_code=404, detail="Ligue introuvable.")
    if lg["owner"] != current_user:
        raise HTTPException(status_code=403, detail="Seul le propriétaire peut supprimer la ligue.")
    delete_league_by_id(league_id, settings)


@router.delete("/{league_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_league(
    league_id: str,
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    lg = get_league_by_id(league_id, settings)
    if not lg:
        raise HTTPException(status_code=404, detail="Ligue introuvable.")

    members = parse_members(lg.get("members", ""))
    if current_user not in members:
        raise HTTPException(status_code=400, detail="Tu n'es pas membre de cette ligue.")
    if lg["owner"] == current_user:
        raise HTTPException(status_code=400, detail="Le propriétaire ne peut pas quitter sa ligue. Supprimez-la.")

    members.remove(current_user)
    update_league_members(league_id, ",".join(members), settings)
