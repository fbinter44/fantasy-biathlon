import streamlit as st
from utils.ui_components import sidebar_menu, user_header

st.set_page_config(
    page_title="MPG Biathlon",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Masquer la sidebar native de Streamlit
hide_sidebar_style = """
    <style>
        [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_sidebar_style, unsafe_allow_html=True)

# Menu personnalisé + header utilisateur
sidebar_menu()
user_header()

# ---------------------------------------------------------
# HERO SECTION
# ---------------------------------------------------------

st.markdown(
    """
    <div style="
        padding: 40px 30px;
        background: linear-gradient(135deg, #1e3c72, #2a5298);
        border-radius: 14px;
        color: white;
        margin-bottom: 35px;
    ">
        <h1 style="margin: 0; font-size: 40px;">🏔️ Fantasy Biathlon — Saison 2025/26</h1>
        <p style="font-size: 20px; opacity: 0.9; margin-top: 8px;">
            Bienvenue sur l'application du Fantasy Biathlon. 
            Crée ton compte, fais tes pronostics, et défie les autres joueurs tout au long de la saison.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# SECTION : POURQUOI JOUER ?
# ---------------------------------------------------------

st.markdown("## 🎯 Le concept")

st.markdown(
    """
    <div style="
        padding: 22px;
        background-color: #f7f9fc;
        border: 1px solid #e0e6ed;
        border-radius: 12px;
        font-size: 17px;
        line-height: 1.6;
        margin-bottom: 30px;
    ">
        <ul style="margin: 0; padding-left: 20px;">
            <li><strong>Pronostique</strong> les classements finaux des biathlètes pour chaque discipline et le général.</li>
            <li><strong>Gagne des points</strong> en fonction de la précision de tes prédictions.</li>
            <li><strong>Suis les résultats officiels</strong> mis à jour automatiquement.</li>
            <li><strong>Affronte les autres joueurs</strong> dans un classement Fantasy.</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# SECTION : APPEL À L’ACTION
# ---------------------------------------------------------

st.markdown("## 🚀 Commence l’aventure")

col1, col2 = st.columns([1, 1])

# --- STYLE GLOBAL POUR LES BOUTONS ---
st.markdown("""
<style>
.big-btn > button {
    width: 100%;
    border-radius: 8px;
    padding: 10px 0;
    font-size: 17px;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

with col1:
    st.markdown(
        """
        <div style="
            padding: 24px;
            background-color: #e8f4ff;
            border-left: 5px solid #1e88e5;
            border-radius: 10px;
            font-size: 18px;
            margin-bottom: 10px;
        ">
            <strong>Connecte-toi</strong>
            pour accéder à tes pronostics et suivre ta progression.
        </div>
        """,
        unsafe_allow_html=True
    )

    # Bouton intégré
    with st.container():
        st.markdown('<div class="big-btn">', unsafe_allow_html=True)
        st.page_link("pages/0_Login.py", label="➡️➡️➡️ 🔐 Se connecter")
        st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown(
        """
        <div style="
            padding: 24px;
            background-color: #e8ffe8;
            border-left: 5px solid #43a047;
            border-radius: 10px;
            font-size: 18px;
            margin-bottom: 10px;
        ">
            <strong>Inscris-toi</strong>
            en quelques secondes et rejoins la compétition.
        </div>
        """,
        unsafe_allow_html=True
    )

    # Bouton intégré
    with st.container():
        st.markdown('<div class="big-btn">', unsafe_allow_html=True)
        st.page_link("pages/0_Login.py", label="👉👉👉 🆕 Créer un compte")
        st.markdown('</div>', unsafe_allow_html=True)
