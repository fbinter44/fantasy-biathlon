import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from scorer.players_score import get_player_row
from utils.ui import sidebar_menu, user_header

sidebar_menu()
user_header()


user = st.session_state.get("user")

if not user:
    st.error("Tu dois être connecté pour accéder à cette page.")
    st.stop()

player = st.session_state["user"]

# Connexion Google Sheets
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
# Formulaire
# -------------------------

st.title("📝 Saisie des pronostics")

player = st.text_input("Ton nom / pseudo")

row_index, row_values = None, None
if player:
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

top5_h = [st.text_input(f"Place {i} (H)", value=existing_top5_h[i-1], key=f"h{i}") for i in range(1, 6)]
top5_f = [st.text_input(f"Place {i} (F)", value=existing_top5_f[i-1], key=f"f{i}") for i in range(1, 6)]

globe_sprint_h = st.text_input("Vainqueur du globe sprint Hommes", value=existing_globe_sprint_h)
globe_sprint_f = st.text_input("Vainqueur du globe sprint Femmes", value=existing_globe_sprint_f)
globe_pursuit_h = st.text_input("Vainqueur du globe poursuite Hommes", value=existing_globe_pursuit_h)
globe_pursuit_f = st.text_input("Vainqueur du globe poursuite Femmes", value=existing_globe_pursuit_f)
globe_individual_h = st.text_input("Vainqueur du globe individuel Hommes", value=existing_globe_individual_h)
globe_individual_f = st.text_input("Vainqueur du globe individuel Femmes", value=existing_globe_individual_f)
globe_mass_h = st.text_input("Vainqueur du globe mass start Hommes", value=existing_globe_mass_start_h)
globe_mass_f = st.text_input("Vainqueur du globe mass start Femmes", value=existing_globe_mass_start_f)

if st.button("💾 Enregistrer mes pronostics"):
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
    
    # 1) On récupère toute la colonne "player"
    players_column = sheet.col_values(1)  # 1 = première colonne

    if player in players_column:
        # 2) Le joueur existe déjà → on met à jour sa ligne
        row_index = players_column.index(player) + 1  # +1 car gspread est 1-based
        sheet.update(f"A{row_index}:H{row_index}", [row_values])
        st.success("Tes pronostics ont été mis à jour ✅")
    else:
        # 3) Nouveau joueur → on ajoute une ligne
        sheet.append_row(row_values)
        st.success("Tes pronostics ont été enregistrés ✅")

