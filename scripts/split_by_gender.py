import json

if __name__ == "__main__":

    with open("biathletes_data/all_athletes.json", encoding="utf-8") as f:
        raw = json.load(f)

    athletes_info = {}
    athletes_h = []
    athletes_f = []
    ignored = []

    for a in raw:
        ibuid = a.get("IBUId")
        family = (a.get("FamilyName") or "").strip()
        given = (a.get("GivenName") or "").strip()
        nat = a.get("NAT")
        gender = a.get("GenderId")
        short = a.get("ShortName")

        # Vérification minimale
        if not ibuid or not family or not given:
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

        if gender == "M":
            athletes_h.append(ibuid)
        elif gender == "W":
            athletes_f.append(ibuid)
        else:
            ignored.append(a)

    # Tri alphabétique
    athletes_h.sort(key=lambda i: (athletes_info[i]["FamilyName"], athletes_info[i]["GivenName"]))
    athletes_f.sort(key=lambda i: (athletes_info[i]["FamilyName"], athletes_info[i]["GivenName"]))

    # Sauvegarde
    with open("biathletes_data/athletes_info.json", "w", encoding="utf-8") as f:
        json.dump(athletes_info, f, indent=2, ensure_ascii=False)

    with open("biathletes_data/athletes_h.json", "w", encoding="utf-8") as f:
        json.dump(athletes_h, f, indent=2, ensure_ascii=False)

    with open("biathletes_data/athletes_f.json", "w", encoding="utf-8") as f:
        json.dump(athletes_f, f, indent=2, ensure_ascii=False)

    print("OK — fichiers régénérés.")
    print(f"Hommes : {len(athletes_h)}")
    print(f"Femmes : {len(athletes_f)}")
    print(f"Ignorés : {len(ignored)}")
