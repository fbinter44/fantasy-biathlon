import json
import os

OUTPUT_FILE = "biathletes_data/athletes_info.json"

if __name__ == "__main__":

    with open("biathletes_data/all_athletes.json", encoding="utf-8") as f:
        raw = json.load(f)

    # On part du fichier existant : un athlète n'en est jamais retiré, sinon il
    # serait écarté des classements recalculés et des pronos déjà enregistrés.
    athletes_info = {}
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            athletes_info = json.load(f)
    previous_ids = set(athletes_info)
    seen_ids = set()
    ignored = []

    for a in raw:
        ibuid = a.get("IBUId")
        family = (a.get("FamilyName") or "").strip()
        given = (a.get("GivenName") or "").strip()
        nat = a.get("NAT")
        gender = a.get("GenderId")
        short = a.get("ShortName")

        # Vérification minimale
        if not ibuid or not family or not given or gender not in ("M", "W"):
            ignored.append(a)
            continue

        athletes_info[ibuid] = {
            "IBUId": ibuid,
            "FamilyName": family,
            "GivenName": given,
            "ShortName": short,
            "NAT": nat,
            "GenderId": gender
        }
        seen_ids.add(ibuid)

    # Seul athletes_info.json est lu par l'app (utils/biathlon_data.py, qui
    # reconstruit lui-même les listes par genre) — pas besoin de fichiers
    # séparés par genre.
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(athletes_info, f, indent=2, ensure_ascii=False)

    print("OK — athletes_info.json régénéré.")
    print(f"Athlètes : {len(athletes_info)}")
    print(f"Nouveaux : {len(seen_ids - previous_ids)}")
    print(f"Conservés (absents de all_athletes.json) : {len(previous_ids - seen_ids)}")
    print(f"Ignorés : {len(ignored)}")
