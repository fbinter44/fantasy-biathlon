import json
from copy import deepcopy
from utils.biathlon_data import DISCIPLINE_MAP


class IBUSeasonResultsBuilder:
    """
    Construit les standings cumulés d'une saison, venue par venue.

    Entrée :
        - une liste de CompetitionVenue (venues)
        - chaque venue contient une liste d'Epreuve
        - chaque Epreuve contient un DataFrame results

    Sortie :
        - un dict timeline[index] = {
              "venue_id": ...,
              "start": date,
              "end": date,
              "general": {Men: {id: pts}, Women: {...}},
              "sprint": {...},
              "pursuit": {...},
              "individual": {...},
              "mass_start": {...},
          }
    """

    def __init__(self, season_code):
        self.season_code = season_code

        # Chargement des infos athlètes (pour déterminer le genre)
        with open("biathletes_data/athletes_info.json", encoding="utf-8") as f:
            self.athletes = json.load(f)

    def _get_gender(self, ibu_id):
        """Retourne 'Men' ou 'Women' selon l'athlète."""
        info = self.athletes.get(ibu_id)
        if not info:
            return None
        return "Men" if info["GenderId"] == "M" else "Women"

    def _init_empty_standings(self):
        """Structure vide pour les standings cumulés."""
        return {
            "general": {"Men": {}, "Women": {}},
            "sprint": {"Men": {}, "Women": {}},
            "pursuit": {"Men": {}, "Women": {}},
            "individual": {"Men": {}, "Women": {}},
            "mass_start": {"Men": {}, "Women": {}},
        }

    def _add_points(self, standings, gender, ibu_id, points, discipline):
        """Ajoute des points dans la structure cumulative."""
        if points is None:
            return

        # Général
        standings["general"][gender][ibu_id] = (
            standings["general"][gender].get(ibu_id, 0) + int(points)
        )

        # Discipline
        if discipline in standings:
            standings[discipline][gender][ibu_id] = (
                standings[discipline][gender].get(ibu_id, 0) + int(points)
            )

    def build(self, venues):
        """
        Construit la timeline des standings cumulés.
        """
        timeline = {}
        cumulative = self._init_empty_standings()

        for idx, venue in enumerate(venues):
            for ep in venue.epreuves:
                df = ep.results
                if df is None:
                    continue

                discipline = DISCIPLINE_MAP.get(ep.discipline)
                if discipline is None:
                    continue

                for _, row in df.iterrows():
                    ibu_id = row["ibu_id"]
                    points = row["points"]
                    gender = self._get_gender(ibu_id)

                    if gender:
                        self._add_points(cumulative, gender, ibu_id, points, discipline)

            # Snapshot profond pour figer l'état après la venue
            timeline[idx] = {
                "venue_id": venue.event_id,
                "start": venue.start_date,
                "end": venue.end_date,
                "standings": deepcopy(cumulative),
            }

        return timeline
