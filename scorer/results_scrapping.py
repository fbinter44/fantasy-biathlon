import requests
import pandas as pd


GENDERS = ["Women", "Men"]

DISCIPLINES = ["General", "Sprint", "Pursuit", "Mass Start", "Individual"]

DISCIPLINE_CODES = {
    "Women": {
        "General": "SWTS",
        "Sprint": "SWSP",
        "Pursuit": "SWPU",
        "Mass Start": "SWMS",
        "Individual": "SWIN"
    },
    "Men": {
        "General": "SMTS",
        "Sprint": "SMSP",
        "Pursuit": "SMPU",
        "Mass Start": "SMMS",
        "Individual": "SMIN"
    }
}


def build_cup_url(season_start, season_end, discipline, language="FR"):
    base_url = "https://bw.biathlonresults.com/modules/sportapi/api/CupResults"

    cup_id = f"BT{season_start}{season_end}SWRLCP__{discipline}"

    url = f"{base_url}?CupId={cup_id}&Language={language}"
    return url


def get_cup_results(gender, discipline):
    if gender not in GENDERS:
        raise ValueError("Please verify the gender.")
    if discipline not in DISCIPLINES:
        raise ValueError("Please verify the discipline.")
    url = build_cup_url(25, 26, DISCIPLINE_CODES[gender][discipline])
    response = requests.get(url)
    data = response.json()

    rows = data["Rows"][:10]  # top 10

    df = pd.DataFrame([{
        "rank": r["Rank"],
        "name": r["Name"],
        "nation": r["Nat"],
        "points": r["Score"]
    } for r in rows])

    return df



if __name__ == "__main__":
    df = get_cup_results("Men", "Mass Start")
    print(df)
