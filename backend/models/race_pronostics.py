from pydantic import BaseModel


class RacePronosticBody(BaseModel):
    ibu_id: str  # IBU ID de l'athlète pronostiqué vainqueur


class RacePronosticsResponse(BaseModel):
    pronos: dict[str, str]  # {race_id: ibu_id}
