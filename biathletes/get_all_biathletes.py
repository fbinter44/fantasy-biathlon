import requests
import json
import time


if __name__ == "__main__":

    BASE_URL = "https://api.biathlonworld.com/content/v1/athletes"
    PAGE_SIZE = 200  # max possible
    page = 1

    all_athletes = []

    while True:
        url = f"{BASE_URL}?page={page}&pageSize={PAGE_SIZE}"
        print("Fetching page", page)

        r = requests.get(url)
        data = r.json()

        # Si la page est vide → on arrête
        if not data:
            break

        all_athletes.extend(data)
        page += 1

        time.sleep(0.2)  # éviter de spammer l’API

    # Sauvegarde
    with open("all_athletes.json", "w", encoding="utf-8") as f:
        json.dump(all_athletes, f, indent=2, ensure_ascii=False)

    print("Total athletes:", len(all_athletes))