import json

if __name__ == "__main__":

    # Chargement du fichier brut
    with open("biathletes\\all_athletes.json", encoding="utf-8") as f:
        raw = json.load(f)

    athletes_info = {}
    athletes_h = []
    athletes_f = []

    for a in raw:
        ibuid = a["IBUId"]
        family = a["FamilyName"].strip()
        given = a["GivenName"].strip()
        nat = a["NAT"]
        gender = a["GenderId"]

        # On construit l'entrée propre
        athletes_info[ibuid] = {
            "IBUId": ibuid,
            "FamilyName": family,
            "GivenName": given,
            "ShortName": a["ShortName"],
            "NAT": nat,
            "GenderId": gender
        }

        # Séparation hommes / femmes
        if gender == "M":
            athletes_h.append(ibuid)
        elif gender == "W":
            athletes_f.append(ibuid)

    # Tri alphabétique par nom + prénom
    athletes_h.sort(key=lambda i: (athletes_info[i]["FamilyName"], athletes_info[i]["GivenName"]))
    athletes_f.sort(key=lambda i: (athletes_info[i]["FamilyName"], athletes_info[i]["GivenName"]))

    # Sauvegarde
    with open("athletes_info.json", "w", encoding="utf-8") as f:
        json.dump(athletes_info, f, indent=2, ensure_ascii=False)

    with open("athletes_h.json", "w", encoding="utf-8") as f:
        json.dump(athletes_h, f, indent=2, ensure_ascii=False)

    with open("athletes_f.json", "w", encoding="utf-8") as f:
        json.dump(athletes_f, f, indent=2, ensure_ascii=False)

    print("OK — fichiers régénérés.")
