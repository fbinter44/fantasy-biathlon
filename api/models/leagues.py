from pydantic import BaseModel
from typing import Optional


class LeagueCreate(BaseModel):
    name: str


class LeagueJoin(BaseModel):
    invite_code: str


class LeagueMember(BaseModel):
    user_id: str
    username: str


class LeagueResponse(BaseModel):
    league_id: str
    name: str
    owner_id: str
    invite_code: str
    members: list[LeagueMember]


class LeagueListItem(BaseModel):
    league_id: str
    name: str
    member_count: int
    is_owner: bool
