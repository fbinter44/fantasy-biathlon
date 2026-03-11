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
from utils.feedback import send_feedback_email


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
# 3) Sommaire
# ---------------------------------------------------------

st.markdown("""
<style>
.anchor-offset {
  position: relative;
  top: -80px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
### 📌 Navigation rapide

- [📄 Informations du compte](#infos)
- [🔒 Changer mon mot de passe](#securite)
- [💬 Feedback & Suggestions](#feedback)
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# 4) Affichage des infos
# ---------------------------------------------------------

st.markdown('<div id="infos" class="anchor-offset"></div>', unsafe_allow_html=True)
st.subheader("📄 Informations du compte")
st.write(f"**Pseudo :** {user_row['username']}")
st.write(f"**Email :** {user_row['email']}")
st.markdown("---")


# ---------------------------------------------------------
# 5) Changement de mot de passe
# ---------------------------------------------------------

st.markdown('<div id="securite" class="anchor-offset"></div>', unsafe_allow_html=True)
# st.markdown('<a id="securite"></a>', unsafe_allow_html=True)
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
# 6) Collecte de feedback
# ---------------------------------------------------------

st.markdown('<div id="feedback" class="anchor-offset"></div>', unsafe_allow_html=True)
st.subheader("💬 Feedback & Suggestions")
st.write("Ton avis compte ! N’hésite pas à partager tes idées ou signaler un bug.")

with st.form("feedback_form"):
    feedback_type = st.selectbox(
        "Type de feedback",
        ["Suggestion", "Bug", "Amélioration", "Autre"]
    )

    subject = st.text_input("Sujet")
    message = st.text_area("Message")

    submitted = st.form_submit_button("Envoyer")

    if submitted:
        user = st.session_state.get("user", "Utilisateur inconnu")
        send_feedback_email(user, feedback_type, subject, message)
        st.success("Merci pour ton feedback !")

st.markdown("---")
