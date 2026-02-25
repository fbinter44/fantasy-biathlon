import streamlit as st
from utils.auth import (
    authenticate,
    create_account,
    request_password_reset,
    reset_password
)
from utils.ui import sidebar_menu, user_header

sidebar_menu()
user_header()


if st.session_state.get("user"):
    st.success(f"Déjà connecté en tant que {st.session_state['user']}")
    st.stop()


st.title("🔐 Connexion / Inscription")

options = ["Se connecter", "Créer un compte"]
if "user" not in st.session_state:
    options.append("Mot de passe oublié")

mode = st.radio("Choisis une option", options)

# ---------------------------------------------------------
# 1) SE CONNECTER
# ---------------------------------------------------------
if mode == "Se connecter":
    identifier = st.text_input("Nom d'utilisateur ou email")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Connexion"):
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

    if st.button("Créer mon compte"):
        ok, msg = create_account(username, email, password)
        if ok:
            st.success(msg)
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

        if st.button("Envoyer le code"):
            ok, result = request_password_reset(email)

            if ok:
                st.success(
                    "Un code de réinitialisation a été généré. "
                    "Comme l’envoi d’email n’est pas encore configuré, "
                    "voici ton code temporaire :"
                )
                st.code(result)
                st.info("Tu peux maintenant entrer ce code dans l’onglet ci-dessous.")
            else:
                st.error(result)

    # --- 3B : RÉINITIALISATION ---
    else:
        email = st.text_input("Ton adresse email")
        code = st.text_input("Code reçu")
        new_password = st.text_input("Nouveau mot de passe", type="password")

        if st.button("Réinitialiser"):
            ok, msg = reset_password(email, code, new_password)

            if ok:
                st.success("Ton mot de passe a été réinitialisé. Tu peux maintenant te connecter.")
            else:
                st.error(msg)