from pydantic import BaseModel
from typing import Optional


class Top5(BaseModel):
    p1: str = ""
    p2: str = ""
    p3: str = ""
    p4: str = ""
    p5: str = ""


class GlobeWinners(BaseModel):
    sprint_h: str = ""
    sprint_f: str = ""
    pursuit_h: str = ""
    pursuit_f: str = ""
    individual_h: str = ""
    individual_f: str = ""
    mass_start_h: str = ""
    mass_start_f: str = ""


class PronosticsResponse(BaseModel):
    user_id: str
    username: str
    top5_h: Top5
    top5_f: Top5
    globes: GlobeWinners


class PronosticsUpdateRequest(BaseModel):
    top5_h: Optional[Top5] = None
    top5_f: Optional[Top5] = None
    globes: Optional[GlobeWinners] = None
