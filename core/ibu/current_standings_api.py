import requests
import pandas as pd

from utils.api_helpers import DISCIPLINE_CODES


class IBUCurrentStandingsAPI:
    """
    Accès aux classements globaux IBU (CupResults).
    """

    BASE_URL = "https://bw.biathlonresults.com/modules/sportapi/api/CupResults"

    def __init__(self, season_code):
        self.season_code = season_code
        self.start = season_code[:2]
        self.end = season_code[2:]

    def _build_url(self, gender, discipline):
        code = DISCIPLINE_CODES[gender][discipline]
        cup_id = f"BT{self.start}{self.end}SWRLCP__{code}"
        return f"{self.BASE_URL}?CupId={cup_id}&Language=EN"

    def get_results(self, gender, discipline):
        url = self._build_url(gender, discipline)
        data = requests.get(url).json()
        rows = data["Rows"][:10]

        return pd.DataFrame(
            {
                "id": [r["IBUId"] for r in rows],
                "rank": [r["Rank"] for r in rows],
                "name": [r["Name"] for r in rows],
                "nation": [r["Nat"] for r in rows],
                "points": [r["Score"] for r in rows],
            }
        )
