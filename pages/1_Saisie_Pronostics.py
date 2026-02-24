import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from scorer.players_score import get_player_row
from utils.ui import sidebar_menu, user_header

# -------------------------
# UI
# -------------------------
sidebar_menu()
user_header()

# Vérification connexion
user = st.session_state.get("user")
if not user:
    st.error("Tu dois être connecté pour accéder à cette page.")
    st.stop()

player = user

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
st.title("📝 Saisie des pronostics")

col_h, col_f = st.columns(2)

# --- HOMMES ---
with col_h:
    st.subheader("🧔 Hommes — Top 5 général")
    top5_h = [
        st.text_input(f"Place {i}", value=existing_top5_h[i-1], key=f"top5_h_{i}")
        for i in range(1, 6)
    ]

    st.subheader("Globes Hommes")
    globe_sprint_h = st.text_input("Globe Sprint", value=existing_globe_sprint_h, key="globe_sprint_h")
    globe_pursuit_h = st.text_input("Globe Poursuite", value=existing_globe_pursuit_h, key="globe_pursuit_h")
    globe_individual_h = st.text_input("Globe Individuel", value=existing_globe_individual_h, key="globe_individual_h")
    globe_mass_h = st.text_input("Globe Mass Start", value=existing_globe_mass_start_h, key="globe_mass_h")

# --- FEMMES ---
with col_f:
    st.subheader("👩 Femmes — Top 5 général")
    top5_f = [
        st.text_input(f"Place {i}", value=existing_top5_f[i-1], key=f"top5_f_{i}")
        for i in range(1, 6)
    ]

    st.subheader("Globes Femmes")
    globe_sprint_f = st.text_input("Globe Sprint", value=existing_globe_sprint_f, key="globe_sprint_f")
    globe_pursuit_f = st.text_input("Globe Poursuite", value=existing_globe_pursuit_f, key="globe_pursuit_f")
    globe_individual_f = st.text_input("Globe Individuel", value=existing_globe_individual_f, key="globe_individual_f")
    globe_mass_f = st.text_input("Globe Mass Start", value=existing_globe_mass_start_f, key="globe_mass_f")

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

# -------------------------
# Sauvegarde
# -------------------------
if st.button("💾 Enregistrer mes pronostics", disabled=not all_filled):

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