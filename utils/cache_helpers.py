import os
import json


CACHE_VENUES_DIR = "cache/cache_venues"
CACHE_RESULTS_DIR = "cache/cache_results"
CACHE_STANDINGS_DIR = "cache/cache_standings"
CACHE_PRONOS_DIR = "cache/cache_pronos"
CACHE_LEAGUES_DIR = "cache/cache_leagues"


def cache_path(dir, file):
    os.makedirs(dir, exist_ok=True)
    return os.path.join(dir, file)
 

def load_from_cache(dir, file):
    """Retourne les données du cache si elles existent, sinon None."""
    path = cache_path(dir, file)

    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        return json.load(f)
    

def save_to_cache(dir, file, data):
    """Sauvegarde les données dans le cache local."""
    path = cache_path(dir, file)
    with open(path, "w") as f:
        json.dump(data, f)
