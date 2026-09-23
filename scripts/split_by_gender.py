import json

if __name__ == "__main__":

    with open("biathletes_data/all_athletes.json", encoding="utf-8") as f:
        raw = json.load(f)

    athletes_info = {}
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

    # Seul athletes_info.json est lu par l'app (utils/biathlon_data.py, qui
    # reconstruit lui-même les listes par genre) — pas besoin de fichiers
    # séparés par genre.
    with open("biathletes_data/athletes_info.json", "w", encoding="utf-8") as f:
        json.dump(athletes_info, f, indent=2, ensure_ascii=False)

    print("OK — athletes_info.json régénéré.")
    print(f"Athlètes : {len(athletes_info)}")
    print(f"Ignorés : {len(ignored)}")
