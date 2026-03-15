import requests
import pandas as pd
import os
import pickle
from datetime import datetime, timezone, timedelta
import json

from utils.api_helpers import DISCIPLINE_CODES
from utils.cache_helpers import CACHE_STANDINGS_DIR


class IBUCurrentStandingsAPI:
    """
    Accès aux classements globaux IBU (CupResults).
    """

    BASE_URL = "https://bw.biathlonresults.com/modules/sportapi/api/CupResults"

    def __init__(self, season_code, client=None):
        self.season_code = season_code
        self.start = season_code[:2]
        self.end = season_code[2:]
        self.client = client

    def _build_url(self, gender, discipline):
        code = DISCIPLINE_CODES[gender][discipline]
        cup_id = f"BT{self.start}{self.end}SWRLCP__{code}"
        return f"{self.BASE_URL}?CupId={cup_id}&Language=EN"

    def cache_path(self, gender, discipline):
        os.makedirs(CACHE_STANDINGS_DIR, exist_ok=True)
        code = DISCIPLINE_CODES[gender][discipline]
        return os.path.join(CACHE_STANDINGS_DIR, f"BT{self.season_code}SWRLCP{code}.pkl")
    
    def should_refresh_standings(self, last_race_end, cache_timestamp):
        now = datetime.now(timezone.utc)

        if last_race_end is None:
            return False

        # Attendre 5h après la fin de la dernière course
        if now < last_race_end + timedelta(hours=5):
            return False

        if cache_timestamp is None:
            return True

        if cache_timestamp < last_race_end:
            return True

        return False

    def get_results(self, gender, discipline, top=10, force_refresh=False):
        cache_path = self.cache_path(gender, discipline)

        cached_df = None
        cache_timestamp = None

        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                data = pickle.load(f)
                cached_df = data["standings"]
                cache_timestamp = data.get("timestamp")

        # Récupérer la dernière course terminée via IBUClient
        last_race_end = self.client.get_last_race_end()

        # Décider si on doit rafraîchir
        if (
            not force_refresh
            and cached_df is not None
            and not self.should_refresh_standings(last_race_end, cache_timestamp)
        ):
            return cached_df

        # Sinon → API
        url = self._build_url(gender, discipline)
        data = requests.get(url).json()
        rows = data["Rows"][:top]

        df = pd.DataFrame({
            "id": [r["IBUId"] for r in rows],
            "rank": [r["Rank"] for r in rows],
            "name": [r["Name"] for r in rows],
            "nation": [r["Nat"] for r in rows],
            "points": [r["Score"] for r in rows],
        })

        with open(cache_path, "wb") as f:
            pickle.dump({
                "standings": df,
                "timestamp": datetime.now(timezone.utc)
            }, f)

        # Mise à jour du fichier de json qui stocke les dates de mise à jour des classements
        if self.should_refresh_standings(last_race_end, cache_timestamp):
            state_file = "users_info/standings_state.json"
            os.makedirs("users_info", exist_ok=True)
            if not os.path.exists(state_file):
                with open(state_file, "w") as f:
                    json.dump({}, f)  # fichier JSON vide
            state = json.load(open(state_file))
            state["results_version"] += 1
            json.dump(state, open(state_file, "w"))

        return df
