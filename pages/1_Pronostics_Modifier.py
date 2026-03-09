import streamlit as st
import gspread
import json
from google.oauth2.service_account import Credentials
from scorer.players_score import get_player_row
from utils.ui_components import sidebar_menu, user_header
from datetime import datetime
from utils.biathlon_data import PRONOS_DEADLINE

# -------------------------
# UI
# -------------------------
st.session_state["current_page"] = "1_Pronostics_Modifier"

sidebar_menu()
user_header()

# Vérification connexion
user = st.session_state.get("user")
if not user:
    st.error("Tu dois être connecté pour accéder à cette page.")
    st.stop()

player = user

deadline_passed = datetime.now() > PRONOS_DEADLINE

if deadline_passed:
    st.error("⛔ La saison a débuté, tu ne peux plus saisir ou modifier tes pronos !")

# -------------------------
# Chargement des athlètes
# -------------------------
with open("biathletes_data/athletes_info.json", encoding="utf-8") as f:
    ATHLETES_INFO = json.load(f)

# Dictionnaire par IBUId
ATHLETES_BY_IBUID = {a["IBUId"]: a for a in ATHLETES_INFO.values()}

# -------------------------
# Drapeaux emoji (fiables partout)
# -------------------------
FLAG = {
    "FRA": "🇫🇷", "NOR": "🇳🇴", "SWE": "🇸🇪", "GER": "🇩🇪", "ITA": "🇮🇹",
    "SUI": "🇨🇭", "AUT": "🇦🇹", "FIN": "🇫🇮", "USA": "🇺🇸", "CAN": "🇨🇦",
    "CZE": "🇨🇿", "SVK": "🇸🇰", "SLO": "🇸🇮", "POL": "🇵🇱", "UKR": "🇺🇦",
    "BLR": "🇧🇾", "RUS": "🇷🇺", "KAZ": "🇰🇿", "JPN": "🇯🇵", "CHN": "🇨🇳",
}

# -------------------------
# Construction des listes internes (IBUId)
# -------------------------
BIATHLETES_H = [""] + [ibu for ibu, a in ATHLETES_BY_IBUID.items() if a["GenderId"] == "M"]
BIATHLETES_F = [""] + [ibu for ibu, a in ATHLETES_BY_IBUID.items() if a["GenderId"] == "W"]

# -------------------------
# Label affiché = drapeau + nom + prénom
# -------------------------
def display_label(ibuid):
    if ibuid == "":
        return ""
    info = ATHLETES_BY_IBUID[ibuid]
    nat = info["NAT"]
    flag = FLAG.get(nat, "🏳️")
    return f"{flag} {info['FamilyName']} {info['GivenName']}"

DISPLAY_H = [display_label(i) for i in BIATHLETES_H]
DISPLAY_F = [display_label(i) for i in BIATHLETES_F]

DISPLAY_TO_IBUID = {display_label(i): i for i in BIATHLETES_H + BIATHLETES_F}

def get_index(lst, value):
    return lst.index(value) if value in lst else 0

# -------------------------
# Connexion Google Sheets
# -------------------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=scope
)

client = gspread.authorize(creds)
sheet = client.open_by_key(st.secrets["sheets"]["sheet_id"]).worksheet("Pronostics")

# -------------------------
# Récupération des valeurs existantes
# -------------------------
row_index, row_values = get_player_row(sheet, player)

if row_values:
    existing_top5_h = row_values[1].split(",")
    existing_top5_f = row_values[2].split(",")
    existing_globe_sprint_h = row_values[3]
    existing_globe_sprint_f = row_values[4]
    existing_globe_pursuit_h = row_values[5]
    existing_globe_pursuit_f = row_values[6]
    existing_globe_individual_h = row_values[7]
    existing_globe_individual_f = row_values[8]
    existing_globe_mass_start_h = row_values[9]
    existing_globe_mass_start_f = row_values[10]
else:
    existing_top5_h = [""] * 5
    existing_top5_f = [""] * 5
    existing_globe_sprint_h = ""
    existing_globe_sprint_f = ""
    existing_globe_pursuit_h = ""
    existing_globe_pursuit_f = ""
    existing_globe_individual_h = ""
    existing_globe_individual_f = ""
    existing_globe_mass_start_h = ""
    existing_globe_mass_start_f = ""

# -------------------------
# Formulaire
# -------------------------
st.title("📝 Voir/Modifier mes pronostics")

col_h, col_f = st.columns(2)

# --- HOMMES ---
with col_h:
    st.subheader("🧔 Hommes — Top 5 général")

    top5_h = []
    used_h = set()
    for i in range(1, 6):
        existing_display = display_label(existing_top5_h[i-1])
        available = [d for d in DISPLAY_H if d not in used_h or d == existing_display]

        selected_display = st.selectbox(
            f"Place {i}",
            available,
            index=get_index(available, existing_display),
            key=f"top5_h_{i}",
            disabled=deadline_passed
        )

        top5_h.append(DISPLAY_TO_IBUID[selected_display])
        used_h.add(selected_display)

    st.subheader("Globes Hommes")

    globe_sprint_h = DISPLAY_TO_IBUID[st.selectbox(
        "Globe Sprint",
        DISPLAY_H,
        index=get_index(DISPLAY_H, display_label(existing_globe_sprint_h)),
        key="globe_sprint_h",
        disabled=deadline_passed
    )]

    globe_pursuit_h = DISPLAY_TO_IBUID[st.selectbox(
        "Globe Poursuite",
        DISPLAY_H,
        index=get_index(DISPLAY_H, display_label(existing_globe_pursuit_h)),
        key="globe_pursuit_h",
        disabled=deadline_passed
    )]

    globe_individual_h = DISPLAY_TO_IBUID[st.selectbox(
        "Globe Individuel",
        DISPLAY_H,
        index=get_index(DISPLAY_H, display_label(existing_globe_individual_h)),
        key="globe_individual_h",
        disabled=deadline_passed
    )]

    globe_mass_h = DISPLAY_TO_IBUID[st.selectbox(
        "Globe Mass Start",
        DISPLAY_H,
        index=get_index(DISPLAY_H, display_label(existing_globe_mass_start_h)),
        key="globe_mass_h",
        disabled=deadline_passed
    )]

# --- FEMMES ---
with col_f:
    st.subheader("👩 Femmes — Top 5 général")

    top5_f = []
    used_f = set()
    for i in range(1, 6):
        existing_display = display_label(existing_top5_f[i-1])
        available = [d for d in DISPLAY_F if d not in used_f or d == existing_display]

        selected_display = st.selectbox(
            f"Place {i}",
            available,
            index=get_index(available, existing_display),
            key=f"top5_f_{i}",
            disabled=deadline_passed
        )

        top5_f.append(DISPLAY_TO_IBUID[selected_display])
        used_f.add(selected_display)


    st.subheader("Globes Femmes")

    globe_sprint_f = DISPLAY_TO_IBUID[st.selectbox(
        "Globe Sprint",
        DISPLAY_F,
        index=get_index(DISPLAY_F, display_label(existing_globe_sprint_f)),
        key="globe_sprint_f",
        disabled=deadline_passed
    )]

    globe_pursuit_f = DISPLAY_TO_IBUID[st.selectbox(
        "Globe Poursuite",
        DISPLAY_F,
        index=get_index(DISPLAY_F, display_label(existing_globe_pursuit_f)),
        key="globe_pursuit_f",
        disabled=deadline_passed
    )]

    globe_individual_f = DISPLAY_TO_IBUID[st.selectbox(
        "Globe Individuel",
        DISPLAY_F,
        index=get_index(DISPLAY_F, display_label(existing_globe_individual_f)),
        key="globe_individual_f",
        disabled=deadline_passed
    )]

    globe_mass_f = DISPLAY_TO_IBUID[st.selectbox(
        "Globe Mass Start",
        DISPLAY_F,
        index=get_index(DISPLAY_F, display_label(existing_globe_mass_start_f)),
        key="globe_mass_f",
        disabled=deadline_passed
    )]

# -------------------------
# Validation
# -------------------------
all_filled = all([
    *top5_h,
    *top5_f,
    globe_sprint_h,
    globe_sprint_f,
    globe_pursuit_h,
    globe_pursuit_f,
    globe_individual_h,
    globe_individual_f,
    globe_mass_h,
    globe_mass_f
])

if not all_filled:
    st.warning("Merci de remplir **tous** les pronostics avant de sauvegarder.")

# Vérification des doublons dans les TOP 5
duplicates_h = len(top5_h) != len(set(top5_h))
duplicates_f = len(top5_f) != len(set(top5_f))

if duplicates_h or duplicates_f:
    if duplicates_h:
        st.error("Tu as sélectionné deux fois le même biathlète dans le TOP 5 Hommes.")
    if duplicates_f:
        st.error("Tu as sélectionné deux fois le même biathlète dans le TOP 5 Femmes.")

# -------------------------
# Sauvegarde
# -------------------------
can_save = all_filled and not deadline_passed and not duplicates_h and not duplicates_f
if st.button("💾 Enregistrer mes pronostics", disabled=not can_save):

    row_values = [
        player,
        ",".join(top5_h),
        ",".join(top5_f),
        globe_sprint_h,
        globe_sprint_f,
        globe_pursuit_h,
        globe_pursuit_f,
        globe_individual_h,
        globe_individual_f,
        globe_mass_h,
        globe_mass_f
    ]

    players_column = sheet.col_values(1)

    if player in players_column:
        row_index = players_column.index(player) + 1
        sheet.update(f"A{row_index}:K{row_index}", [row_values])
        st.success("Tes pronostics ont été mis à jour ✅")
    else:
        sheet.append_row(row_values)
        st.success("Tes pronostics ont été enregistrés ✅")