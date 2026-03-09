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

st.title("🏠 Accueil MPG Biathlon")

st.write("Bienvenue sur l'application !")