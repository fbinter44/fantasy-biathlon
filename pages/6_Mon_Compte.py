"""
Page : Mon Compte

Permet à l'utilisateur :
- de voir son nom d'utilisateur
- de changer son mot de passe
"""

import streamlit as st
import bcrypt
import pandas as pd

from utils.ui_components import sidebar_menu, user_header
from utils.sheets import get_sheet, update_cell


# ---------------------------------------------------------
# 1) Configuration de la page
# ---------------------------------------------------------

st.session_state["current_page"] = "6_Mon_Compte"
st.set_page_config(page_title="Mon Compte", layout="wide")

sidebar_menu()
user_header()

user = st.session_state.get("user")
if not user:
    st.error("Tu dois être connecté pour accéder à cette page.")
    st.stop()

st.title("👤 Mon Compte")


# ---------------------------------------------------------
# 2) Chargement des données utilisateur
# ---------------------------------------------------------

sheet = get_sheet("Users")
records = sheet.get_all_records()

df_users = pd.DataFrame(records)
user_data = df_users[df_users["username"] == user]
if user_data.empty:
    st.error("Utilisateur introuvable dans la database.")
    st.stop()
row_index = user_data.index[0] + 2
user_row = user_data.iloc[0]


# ---------------------------------------------------------
# 3) Affichage des infos
# ---------------------------------------------------------

st.subheader("📄 Informations du compte")
st.write(f"**Pseudo :** {user_row['username']}")
st.write(f"**Email :** {user_row['email']}")
st.markdown("---")


# ---------------------------------------------------------
# 4) Changement de mot de passe
# ---------------------------------------------------------

st.subheader("🔐 Changer mon mot de passe")

# Formulaire dédié au changement de mot de passe
# La clé "change_password_form" garantit une identité stable du formulaire
with st.form("change_password"):
    old_pwd = st.text_input("Ancien mot de passe", type="password", key="old_pwd_input")
    new_pwd = st.text_input("Nouveau mot de passe", type="password", key="new_pwd_input")
    confirm_pwd = st.text_input("Confirmer le nouveau mot de passe", type="password", key="confirm_pwd_input")

    # Bouton de validation du formulaire
    # La clé "submit_new_password" évite les collisions avec d'autres boutons
    submit_pwd = st.form_submit_button("Mettre à jour", key="submit_new_password")

    if submit_pwd:
        # Vérifications basiques côté client
        if not bcrypt.checkpw(old_pwd.encode(), user_row["password_hash"].encode()):
            st.error("Ancien mot de passe incorrect.")
        elif new_pwd != confirm_pwd:
            st.error("Les mots de passe ne correspondent pas.")
        elif len(new_pwd) < 6:
            st.error("Le mot de passe doit contenir au moins 6 caractères.")
        else:
            new_hash = bcrypt.hashpw(new_pwd.encode(), bcrypt.gensalt()).decode()
            update_cell("Users", row_index, 3, new_hash)

            st.success("Mot de passe mis à jour avec succès !")

st.markdown("---")

# ---------------------------------------------------------
# SECTION : Préférences (placeholder)
# ---------------------------------------------------------
st.subheader("⚙️ Préférences (à venir)")
st.info("Cette section permettra bientôt de personnaliser ton expérience (thème, affichage, notifications…).")
