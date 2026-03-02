from datetime import datetime
import json

PRONOS_DEADLINE = datetime(2026, 10, 24, 23, 59)

with open("biathletes/athletes_info.json", encoding="utf-8") as f:
    ATHLETES_INFO = json.load(f)

ATHLETES_BY_IBUID = {a["IBUId"]: a for a in ATHLETES_INFO.values()}

nats = sorted({a["NAT"] for a in ATHLETES_BY_IBUID.values()})

FLAG = {
    "AND": "🇦🇩",
    "ARG": "🇦🇷",
    "ARM": "🇦🇲",
    "AUS": "🇦🇺",
    "AUT": "🇦🇹",
    "BEL": "🇧🇪",
    "BIH": "🇧🇦",
    "BLR": "🇧🇾",
    "BRA": "🇧🇷",
    "BUL": "🇧🇬",
    "CAN": "🇨🇦",
    "CHI": "🇨🇱",
    "CHN": "🇨🇳",
    "CRO": "🇭🇷",
    "CZE": "🇨🇿",
    "DEN": "🇩🇰",
    "ESP": "🇪🇸",
    "EST": "🇪🇪",
    "FIN": "🇫🇮",
    "FRA": "🇫🇷",
    "GBR": "🇬🇧",
    "GEO": "🇬🇪",
    "GER": "🇩🇪",
    "GRE": "🇬🇷",
    "HUN": "🇭🇺",
    "IND": "🇮🇳",
    "IRL": "🇮🇪",
    "ITA": "🇮🇹",
    "JPN": "🇯🇵",
    "KAZ": "🇰🇿",
    "KEN": "🇰🇪",
    "KGZ": "🇰🇬",
    "KOR": "🇰🇷",
    "LAT": "🇱🇻",
    "LIE": "🇱🇮",
    "LTU": "🇱🇹",
    "LUX": "🇱🇺",
    "MAR": "🇲🇦",
    "MDA": "🇲🇩",
    "MEX": "🇲🇽",
    "MGL": "🇲🇳",
    "MKD": "🇲🇰",
    "NED": "🇳🇱",
    "NOR": "🇳🇴",
    "NZL": "🇳🇿",
    "POL": "🇵🇱",
    "POR": "🇵🇹",
    "PUR": "🇵🇷",
    "ROU": "🇷🇴",
    "RUS": "🇷🇺",
    "SLO": "🇸🇮",
    "SRB": "🇷🇸",
    "SUI": "🇨🇭",
    "SVK": "🇸🇰",
    "SWE": "🇸🇪",
    "THA": "🇹🇭",
    "TPE": "🇹🇼",
    "TUR": "🇹🇷",
    "UKR": "🇺🇦",
    "USA": "🇺🇸",
    "UZB": "🇺🇿",

    # Codes historiques / spéciaux → fallback
    "BRT": "🏳️",  # Bretagne ? (jamais un code ISO)
    "CIS": "🏳️",  # Communauté États Indépendants (post-URSS)
    "FRG": "🇩🇪",  # Allemagne de l'Ouest → Allemagne moderne
    "GDR": "🇩🇪",  # Allemagne de l'Est → Allemagne moderne
    "GRL": "🇬🇱",  # Groenland (territoire, pas ISO indépendant)
    "LIB": "🇱🇧",  # Probablement erreur pour LBN (Liban)
    "ROM": "🇷🇴",  # Ancien code pour Roumanie → ROU
    "TCH": "🇨🇿",  # Tchécoslovaquie → République Tchèque
    "TST": "🏳️",  # Inconnu (test ?)
    "URS": "🏳️",  # URSS (pas de drapeau emoji)
    "YUG": "🏳️",  # Yougoslavie (pas de drapeau emoji)
}

VENUES_NAMES = {
    "Swedish National Biathlon Arena": "Oestersund",
    "Biathlon Stadium Hochfilzen": "Hochfilzen",
    "Le Grand-Bornand Biathlon Arena": "Le Grand-Bornand",
    "ARENA am Rennsteig": "Oberhof",
    "Chiemgau Arena": "Ruhpolding",
    "Vysocina Arena": "Nove Mesto",
    "Biathlon Stadium Kontiolahti": "Kontiolahti",
    "Tehvandi Sport Center": "Otepaa",
    "Holmenkollen": "Oslo Holmenkollen",
}

def athlete_label(ibuid):
    if not ibuid or ibuid not in ATHLETES_BY_IBUID:
        return ""
    info = ATHLETES_BY_IBUID[ibuid]
    flag = FLAG.get(info["NAT"], "🏳️")
    return f"{flag} {info['FamilyName']} {info['GivenName']}"

def format_top5(csv_string):
    if not csv_string:
        return ""
    ibuids = csv_string.split(",")
    return ", ".join(athlete_label(i) for i in ibuids if i)

def split_top5(csv_string):
    if not csv_string:
        return ["", "", "", "", ""]
    items = csv_string.split(",")
    items += [""] * (5 - len(items))  # sécurité si moins de 5
    return items[:5]
