import requests
import pandas as pd

from utils.scrapping_helpers import GENDERS, DISCIPLINES, DISCIPLINE_CODES


def build_cup_url(season_start, season_end, discipline, language="FR"):
    base_url = "https://bw.biathlonresults.com/modules/sportapi/api/CupResults"

    cup_id = f"BT{season_start}{season_end}SWRLCP__{discipline}"

    url = f"{base_url}?CupId={cup_id}&Language={language}"
    return url


def get_cup_results(gender: str, discipline: str, season_code: str = "2526"):
    """
    Récupère le top 10 d’un classement de coupe (général ou petit globe).

    gender: "Men" ou "Women"
    discipline: "General", "Sprint", "Pursuit", "Mass Start", "Individual"
    season_code: "2526", "2627", etc.
    """
    if gender not in GENDERS:
        raise ValueError("Please verify the gender.")
    if discipline not in DISCIPLINES:
        raise ValueError("Please verify the discipline.")

    season_start = int(season_code[:2])
    season_end = int(season_code[2:])

    discipline_code = DISCIPLINE_CODES[gender][discipline]
    url = build_cup_url(season_start, season_end, discipline_code)

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    rows = data["Rows"][:10]  # top 10

    df = pd.DataFrame(
        [
            {
                "id": r["IBUId"],
                "rank": r["Rank"],
                "name": r["Name"],
                "nation": r["Nat"],
                "points": r["Score"],
            } 
            for r in rows
        ]
    )

    return df
