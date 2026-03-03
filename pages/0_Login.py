import streamlit as st
from utils.auth import (
    authenticate,
    create_account,
    request_password_reset,
    reset_password
)
from utils.ui import sidebar_menu, user_header

# ---------------------------------------------------------
# Identification de la page (pour garder le menu Pronostics ouvert/fermé)
# ---------------------------------------------------------
st.session_state["current_page"] = "0_Login"

# ---------------------------------------------------------
# Barre latérale + header utilisateur
# (affichés même sur la page Login pour cohérence globale)
# ---------------------------------------------------------
sidebar_menu()
user_header()

# ---------------------------------------------------------
# Si l'utilisateur est déjà connecté → inutile d'afficher le formulaire
# ---------------------------------------------------------
if st.session_state.get("user"):
    st.success(f"Déjà connecté en tant que {st.session_state['user']}")
    st.stop()

# ---------------------------------------------------------
# Titre + choix du mode (connexion / création / reset)
# ---------------------------------------------------------
st.title("🔐 Connexion / Inscription")

# Forcer le mode après création de compte
if "login_mode" in st.session_state:
    st.session_state["mode"] = st.session_state["login_mode"]

# Les trois modes possibles de la page
options = ["Se connecter", "Créer un compte", "Mot de passe oublié"]
mode = st.radio(
    "Choisis une option",
    options,
    key="mode"
)

# ---------------------------------------------------------
# 1) SE CONNECTER
# ---------------------------------------------------------
if mode == "Se connecter":
    identifier = st.text_input(
        "Nom d'utilisateur ou email",
        value=st.session_state.get("prefill_identifier", "")
    )
    password = st.text_input("Mot de passe", type="password")

    if st.button("Connexion", key="login_btn"):
        ok, result = authenticate(identifier, password)

        if ok:
            st.session_state["user"] = result  # result = username normalisé
            st.success("Connexion réussie")
            st.switch_page("pages/3_Classement.py")
        else:
            st.error(result)

# ---------------------------------------------------------
# 2) CRÉER UN COMPTE
# ---------------------------------------------------------
elif mode == "Créer un compte":
    username = st.text_input("Nom d'utilisateur")
    email = st.text_input("Adresse email")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Créer mon compte", key="create_btn"):
        ok, msg = create_account(username, email, password)
        if ok:
            st.success(msg)
            # Pré-remplissage automatique
            st.session_state["prefill_identifier"] = username or email
            # Retour automatique sur "Se connecter"
            st.session_state["login_mode"] = "Se connecter"
            st.rerun()
        else:
            st.error(msg)

# ---------------------------------------------------------
# 3) MOT DE PASSE OUBLIÉ
# ---------------------------------------------------------
else:
    st.subheader("📩 Réinitialisation du mot de passe")

    reset_mode = st.radio(
        "Que veux-tu faire ?",
        ["Demander un code", "Réinitialiser mon mot de passe"]
    )

    # --- 3A : DEMANDE DE CODE ---
    if reset_mode == "Demander un code":
        email = st.text_input("Ton adresse email")
        if st.button("Envoyer le code", key="send_code_btn"):
            ok, result = request_password_reset(email)
            if ok:
                st.success("Un code de réinitialisation a été généré.")
                st.code(result)
                st.info("Tu peux maintenant entrer ce code dans l’onglet ci-dessous.")
            else:
                st.error(result)

    # --- 3B : RÉINITIALISATION ---
    else:
        email = st.text_input("Ton adresse email")
        code = st.text_input("Code reçu")
        new_password = st.text_input("Nouveau mot de passe", type="password")
        if st.button("Réinitialiser", key="reset_btn"):
            ok, msg = reset_password(email, code, new_password)
            if ok:
                st.success("Ton mot de passe a été réinitialisé. Tu peux maintenant te connecter.")
            else:
                st.error(msg)
