"""
Composants UI globaux de l'application :
- Menu latéral (sidebar)
- Barre utilisateur (header)
- Gestion centralisée de la déconnexion
"""

import streamlit as st
from datetime import datetime

from utils.biathlon_data import PRONOS_DEADLINE


# ---------------------------------------------------------
# 1) Groupes de pages (constants)
# ---------------------------------------------------------

PRONOSTICS_PAGES = [
    "1_Pronostics_Modifier",
    "2_Pronostics_Tous",
    "2b_Pronostics_Biathlete"
]

STANDINGS_PAGES = [
    "3_Classement",
    "3b_Evolution_Classement",
]


# ---------------------------------------------------------
# 2) Déconnexion centralisée
# ---------------------------------------------------------

def logout():
    """Efface la session et recharge l'application."""
    st.session_state.clear()
    st.rerun()


# ---------------------------------------------------------
# 3) Menu latéral (sidebar)
# ---------------------------------------------------------

def sidebar_menu():
    """Affiche le menu latéral en fonction de l'état de connexion."""
    st.sidebar.title("Navigation")

    user = st.session_state.get("user")
    current_page = st.session_state.get("current_page", "")

    pronostics_expanded = current_page in PRONOSTICS_PAGES
    standings_expanded = current_page in STANDINGS_PAGES

    # Pages toujours visible
    st.sidebar.page_link("App.py", label="🏠 Accueil")
    st.sidebar.page_link("pages/5_Reglement.py", label="📘 Règlement")

    if user:
        # --- Section Pronostics ---
        with st.sidebar.expander("📌 Pronostics", expanded=pronostics_expanded):
            st.page_link("pages/1_Pronostics_Modifier.py", label="Voir/Modifier mes pronos")
            st.page_link("pages/2_Pronostics_Tous.py", label="Tous les pronos")
            st.page_link("pages/2b_Pronostics_Biathlete.py", label="Focus Biathlète")

        # --- Section Classement ---
        with st.sidebar.expander("📈 Classement", expanded=standings_expanded):
            st.page_link("pages/3_Classement.py", label="Détails du classement")
            st.page_link("pages/3b_Evolution_Classement.py", label="Évolution du classement")

        # Autres pages
        st.sidebar.page_link("pages/4_Resultats_Officiels.py", label="📜 Résultats officiels")
        st.sidebar.page_link("pages/6_Mon_Compte.py", label="👤 Mon Compte")

        # Déconnexion
        if st.sidebar.button("Se déconnecter"):
            logout()

    else:
        # Pages visibles uniquement si déconnecté
        st.sidebar.page_link("pages/0_Login.py", label="🔐 Connexion / Inscription")


# ---------------------------------------------------------
# 4) Barre utilisateur (header)
# ---------------------------------------------------------

def user_header():
    """Affiche une barre utilisateur en haut de la page."""
    # CSS local
    st.markdown(
        """
        <style>
        .user-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
        }
        .user-circle {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background-color: #4A90E2;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-left: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    user = st.session_state.get("user")

    col1, col2 = st.columns([0.8, 0.2])

    with col1:
        if user:
            initial = user[0].upper()
            st.markdown(
                f"""
                <div class="user-bar">
                    <div>Connecté en tant que <strong>{user}</strong></div>
                    <div class="user-circle">{initial}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown("<em>Non connecté</em>", unsafe_allow_html=True)

    with col2:
        if user:
            if st.button("Déconnexion", key="logout_button_header"):
                logout()


def page_title_with_feedback(title: str):
    # NOT USED FOR NOW, WILL BE USEFUL IF I MANAGE TO STAY CONNECTED WHEN SWITCHING PAGES
    current_page = st.session_state.get("current_page")

    # Pas de bouton sur la page Mon Compte
    if current_page == "6_Mon_Compte":
        st.markdown(f"<h1 style='display:flex; align-items:center;'>{title}</h1>", unsafe_allow_html=True)
        return

    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap:10px;">
            <h1 style="margin:0;">{title}</h1>
            <a href="Mon_Compte" title="Clique ici pour partager du feedback"
               style="text-decoration:none; font-size:28px; cursor:pointer;">
                💡
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_deadline_banner():
    now = datetime.now()
    remaining = PRONOS_DEADLINE - now

    if remaining.total_seconds() <= 0:
        st.markdown(
            """
            <div style="
                padding: 14px 18px;
                background-color: #ffe5e5;
                border-left: 5px solid #d32f2f;
                border-radius: 6px;
                margin-bottom: 25px;
                font-size: 17px;
            ">
                🔒 <strong>La saisie des pronostics est maintenant fermée.</strong>
            </div>
            """,
            unsafe_allow_html=True
        )
        return True

    # --- Temps restant ---
    days = remaining.days
    hours = remaining.seconds // 3600
    minutes = (remaining.seconds % 3600) // 60

    # --- Mode alerte si < 24h ---
    alert_mode = remaining.total_seconds() < 24 * 3600

    bg = "#fff4e5" if not alert_mode else "#fff0f0"
    border = "#ffa726" if not alert_mode else "#e53935"

    st.markdown(
        f"""
        <div style="
            padding: 14px 18px;
            background-color: {bg};
            border-left: 5px solid {border};
            border-radius: 6px;
            margin-bottom: 25px;
            font-size: 17px;
        ">
            ⏳ <strong>Clôture des pronos dans :</strong>
            {days} jours {hours}h {minutes}m
        </div>
        """,
        unsafe_allow_html=True
    )

    return False
