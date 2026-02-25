import json

if __name__ == "__main__":

    with open("biathletes\\all_athletes.json", encoding="utf-8") as f:
        data = json.load(f)

    athletes_h = []
    athletes_f = []
    athletes_info = {}

    for a in data:
        short = a["ShortName"]
        gender = a["GenderId"]
        nat = a["NAT"]
        ibuid = a["IBUId"]

        # Stockage des infos
        athletes_info[short] = {
            "IBUId": ibuid,
            "NAT": nat,
            "GenderId": gender
        }

        # Séparation hommes / femmes
        if gender == "M":
            athletes_h.append(short)
        else:
            athletes_f.append(short)

    # Tri alphabétique
    athletes_h.sort()
    athletes_f.sort()

    # Sauvegarde
    json.dump(athletes_h, open("athletes_h.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump(athletes_f, open("athletes_f.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump(athletes_info, open("athletes_info.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    print("OK !")