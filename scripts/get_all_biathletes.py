import requests
import json
import time

BASE_URL = "https://api.biathlonworld.com/content/v1/athletes"
PAGE_SIZE = 200
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

    with open("biathletes_data\\all_athletes.json", "w", encoding="utf-8") as f:
        json.dump(all_athletes, f, indent=2, ensure_ascii=False)

    print("Total athletes:", len(all_athletes))
