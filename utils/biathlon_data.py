"""
Données statiques et helpers liés au domaine du biathlon.

Responsabilités :
- Chargement des données athlètes (JSON statique)
- Indexation par IBUId
- Mapping des drapeaux par code nation
- Mapping des noms de sites → noms simplifiés
- Helpers pour formater les labels athlètes et les TOP5
"""

from datetime import datetime
import json
from pathlib import Path


# ---------------------------------------------------------
# 1) DEADLINE DES PRONOS
# ---------------------------------------------------------

PRONOS_DEADLINE = datetime(2026, 10, 12, 23, 59)


# ---------------------------------------------------------
# 2) CHARGEMENT DES DONNÉES ATHLÈTES
# ---------------------------------------------------------

ATHLETES_FILE = Path("biathletes_data/athletes_info.json")

try:
    with ATHLETES_FILE.open(encoding="utf-8") as f:
        ATHLETES_INFO: dict[str, dict] = json.load(f)
except FileNotFoundError:
    ATHLETES_INFO = {}
    print(f"⚠️ Fichier introuvable : {ATHLETES_FILE}")


# Index par IBUId (accès rapide)
ATHLETES_BY_IBUID = {
    a["IBUId"]: a for a in ATHLETES_INFO.values()
}


# ---------------------------------------------------------
# 3) MAPPING DES DRAPEAUX
# ---------------------------------------------------------

FLAGS = {
    # Codes ISO classiques
    "AND": "🇦🇩", "ARG": "🇦🇷", "ARM": "🇦🇲", "AUS": "🇦🇺", "AUT": "🇦🇹",
    "BEL": "🇧🇪", "BIH": "🇧🇦", "BLR": "🇧🇾", "BRA": "🇧🇷", "BUL": "🇧🇬",
    "CAN": "🇨🇦", "CHI": "🇨🇱", "CHN": "🇨🇳", "CRO": "🇭🇷", "CZE": "🇨🇿",
    "DEN": "🇩🇰", "ESP": "🇪🇸", "EST": "🇪🇪", "FIN": "🇫🇮", "FRA": "🇫🇷",
    "GBR": "🇬🇧", "GEO": "🇬🇪", "GER": "🇩🇪", "GRE": "🇬🇷", "HUN": "🇭🇺",
    "IND": "🇮🇳", "IRL": "🇮🇪", "ITA": "🇮🇹", "JPN": "🇯🇵", "KAZ": "🇰🇿",
    "KEN": "🇰🇪", "KGZ": "🇰🇬", "KOR": "🇰🇷", "LAT": "🇱🇻", "LIE": "🇱🇮",
    "LTU": "🇱🇹", "LUX": "🇱🇺", "MAR": "🇲🇦", "MDA": "🇲🇩", "MEX": "🇲🇽",
    "MGL": "🇲🇳", "MKD": "🇲🇰", "NED": "🇳🇱", "NOR": "🇳🇴", "NZL": "🇳🇿",
    "POL": "🇵🇱", "POR": "🇵🇹", "PUR": "🇵🇷", "ROU": "🇷🇴", "RUS": "🇷🇺",
    "SLO": "🇸🇮", "SRB": "🇷🇸", "SUI": "🇨🇭", "SVK": "🇸🇰", "SWE": "🇸🇪",
    "THA": "🇹🇭", "TPE": "🇹🇼", "TUR": "🇹🇷", "UKR": "🇺🇦", "USA": "🇺🇸",
    "UZB": "🇺🇿",

    # Codes historiques / spéciaux
    "BRT": "🏳️", "CIS": "🏳️", "FRG": "🇩🇪", "GDR": "🇩🇪",
    "GRL": "🇬🇱", "LIB": "🇱🇧", "ROM": "🇷🇴", "TCH": "🇨🇿",
    "TST": "🏳️", "URS": "🏳️", "YUG": "🏳️",
}


# ---------------------------------------------------------
# 4) MAPPING DES SITES
# ---------------------------------------------------------

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


# ---------------------------------------------------------
# 5) HELPERS
# ---------------------------------------------------------

COLUMN_RENAME = {
    "player": "Joueur",
    "top5_h": "Top 5 Hommes",
    "top5_f": "Top 5 Femmes",
    "globe_sprint_h": "Sprint H",
    "globe_sprint_f": "Sprint F",
    "globe_pursuit_h": "Poursuite H",
    "globe_pursuit_f": "Poursuite F",
    "globe_individual_h": "Individuel H",
    "globe_individual_f": "Individuel F",
    "globe_mass_start_h": "Mass Start H",
    "globe_mass_start_f": "Mass Start F",
}

GLOBE_COLS = [
        "Sprint H", "Sprint F",
        "Poursuite H", "Poursuite F",
        "Individuel H", "Individuel F",
        "Mass Start H", "Mass Start F",
    ]

RELAY_IDS = ["RL", "SR"]

GENDERS_CODES = {"SW": "Women", "SM": "Men"}

NB_VENUES_BY_SEASON = {
    '2526': 9,
    '2627': 10,
    '2728': 9
}

DISCIPLINE_MAP = {
    "SP": "sprint",
    "PU": "pursuit",
    "MS": "mass_start",
    "IN": "individual",
    "SI": "individual",   # certains formats individuels utilisent SI
}

DISCIPLINES_DISPLAY = [
    ("general", "Classement Général"),
    ("sprint", "Sprint"),
    ("pursuit", "Poursuite"),
    ("individual", "Individuel"),
    ("mass_start", "Mass Start")
]

DISCIPLINES_WINNERS = {
    "general": "top",
    "sprint": "sprint_winners",
    "pursuit": "pursuit_winners",
    "individual": "individual_winners",
    "mass_start": "mass_start_winners",
}


def athlete_label(ibuid: str) -> str:
    """Retourne un label lisible : '🇫🇷 Fillon Maillet Quentin'."""
    if not ibuid or ibuid not in ATHLETES_BY_IBUID:
        return ""
    info = ATHLETES_BY_IBUID[ibuid]
    flag = FLAGS.get(info["NAT"], "🏳️")
    return f"{flag} {info['FamilyName']} {info['GivenName']}"


# Séparation hommes / femmes
BIATHLETES_H = [ibu for ibu, a in ATHLETES_BY_IBUID.items() if a["GenderId"] == "M"]
BIATHLETES_F = [ibu for ibu, a in ATHLETES_BY_IBUID.items() if a["GenderId"] == "W"]

DISPLAY_H = [""] + [athlete_label(i) for i in BIATHLETES_H]
DISPLAY_F = [""] + [athlete_label(i) for i in BIATHLETES_F]

DISPLAY_TO_IBUID = {athlete_label(i): i for i in BIATHLETES_H + BIATHLETES_F}
DISPLAY_TO_IBUID[""] = ""


def format_top5(csv_string: str) -> str:
    """Transforme 'A,B,C,D,E' → '🇫🇷 A, 🇳🇴 B, ...'."""
    if not csv_string:
        return ""
    ibuids = csv_string.split(",")
    return ", ".join(athlete_label(i) for i in ibuids if i)


def split_top5(csv_string: str) -> list[str]:
    """Transforme 'A,B,C' → ['A','B','C','','']."""
    if not csv_string:
        return ["", "", "", "", ""]
    items = csv_string.split(",")
    items += [""] * (5 - len(items))
    return items[:5]


def ids_to_names(df, ids):
    return set(df[df["id"].isin(ids)]["name"].tolist())


def get_index(lst, value):
    return lst.index(value) if value in lst else 0
