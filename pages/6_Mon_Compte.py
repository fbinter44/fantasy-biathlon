import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from utils.ui import sidebar_menu, user_header
import pandas as pd


st.session_state["current_page"] = "6_Mon_Compte"

st.set_page_config(page_title="Mon Compte", layout="wide")

sidebar_menu()
user_header()

user = st.session_state.get("user")
if not user:
    st.error("Tu dois être connecté pour accéder à cette page.")
    st.stop()

st.title("👤 Mon Compte")

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
sheet = client.open_by_key(st.secrets["sheets"]["sheet_id"]).worksheet("Users")

# Récupération des infos utilisateur
records = sheet.get_all_records()
df_users = pd.DataFrame(records)
user_row = df_users[df_users["username"] == user].iloc[0]

# --- SECTION INFOS ---
st.subheader("📄 Informations du compte")
st.write(f"**Pseudo :** {user_row['username']}")
st.write(f"**Email :** {user_row['email']}")

st.markdown("---")

# --- SECTION CHANGEMENT DE MOT DE PASSE ---
st.subheader("🔐 Changer mon mot de passe")

with st.form("change_password"):
    old_pwd = st.text_input("Ancien mot de passe", type="password")
    new_pwd = st.text_input("Nouveau mot de passe", type="password")
    confirm_pwd = st.text_input("Confirmer le nouveau mot de passe", type="password")
    submit_pwd = st.form_submit_button("Mettre à jour")

    if submit_pwd:
        if old_pwd != user_row["password"]:
            st.error("Ancien mot de passe incorrect.")
        elif new_pwd != confirm_pwd:
            st.error("Les mots de passe ne correspondent pas.")
        elif len(new_pwd) < 6:
            st.error("Le mot de passe doit contenir au moins 6 caractères.")
        else:
            # Mise à jour dans Google Sheets
            cell = sheet.find(user_row["email"])
            sheet.update_cell(cell.row, df_users.columns.get_loc("password") + 1, new_pwd)
            st.success("Mot de passe mis à jour avec succès !")

st.markdown("---")

# --- SECTION PREFERENCES ---
st.subheader("⚙️ Préférences (à venir)")
st.info("Cette section permettra bientôt de personnaliser ton expérience (thème, affichage, notifications…).")