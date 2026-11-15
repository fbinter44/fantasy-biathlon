import requests
import json
import os
import time

BASE_URL = "https://api.biathlonworld.com/content/v1/athletes"
OUTPUT_FILE = "biathletes_data/all_athletes.json"
PAGE_SIZE = 200  # l'API plafonne de toute façon à 20 par page
RETRY_DELAY = 2
MAX_RETRIES = 5

def fetch_page(page):
    url = f"{BASE_URL}?page={page}&pageSize={PAGE_SIZE}"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = requests.get(url, timeout=10)

            if r.status_code == 429:
                print("Rate limit atteint → pause 5 sec…")
                time.sleep(5)
                continue

            r.raise_for_status()
            data = r.json()

            if not isinstance(data, list):
                print("Format inattendu :", data)
                return []

            return data

        except Exception as e:
            print(f"Erreur page {page} (tentative {attempt}/{MAX_RETRIES}) :", e)
            time.sleep(RETRY_DELAY)

    print(f"Échec définitif pour la page {page}")
    return []

if __name__ == "__main__":
    all_athletes = []
    page = 1

    while True:
        print(f"Fetching page {page}…")
        data = fetch_page(page)

        if not data:
            break

        all_athletes.extend(data)
        page += 1
        time.sleep(0.2)

    print("Total athletes:", len(all_athletes))

    # Fusion avec la version précédente : l'IBU retire parfois de son annuaire
    # des athlètes encore présents dans ses résultats de course — on ne
    # supprime donc jamais personne, on ajoute et on met à jour.
    previous = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            previous = json.load(f)

    merged = {a.get("IBUId"): a for a in previous if a.get("IBUId")}
    fetched = {a.get("IBUId"): a for a in all_athletes if a.get("IBUId")}
    added = len(fetched.keys() - merged.keys())
    kept = len(merged.keys() - fetched.keys())
    merged.update(fetched)

    result = sorted(merged.values(), key=lambda a: ((a.get("FamilyName") or "").strip().upper(), a.get("GivenName") or "", a["IBUId"]))
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Fusion : {len(result)} athlètes ({added} nouveaux, {kept} conservés de l'ancienne version absents de l'API)")
