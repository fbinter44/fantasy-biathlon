"""
Module utilitaire pour accéder aux différentes feuilles Google Sheets.

Responsabilités :
- Initialisation du client Google Sheets
- Accès simplifié aux worksheets
- Fonctions utilitaires de lecture/écriture
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials


# ---------------------------------------------------------
# 1) Initialisation du client Google Sheets
# ---------------------------------------------------------

def _get_gspread_client():
    """
    Initialise et retourne un client gspread authentifié.
    Utilise les credentials stockés dans st.secrets.
    """
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    return gspread.authorize(creds)


# ---------------------------------------------------------
# 2) Accès à une worksheet
# ---------------------------------------------------------

def get_sheet(name: str):
    """
    Retourne une worksheet par son nom.
    Exemple : get_sheet("Pronostics")
    """
    client = _get_gspread_client()
    sheet_id = st.secrets["sheets"]["sheet_id"]
    return client.open_by_key(sheet_id).worksheet(name)


# ---------------------------------------------------------
# 3) Fonctions utilitaires
# ---------------------------------------------------------

def read_all(name: str):
    """
    Lit toutes les lignes d'une feuille et retourne une liste de dicts.
    Equivalent à sheet.get_all_records().
    """
    sheet = get_sheet(name)
    return sheet.get_all_records()


def append_row(name: str, row: list):
    """
    Ajoute une ligne à la fin de la feuille.
    """
    sheet = get_sheet(name)
    sheet.append_row(row)


def update_cell(name: str, row: int, col: int, value):
    """
    Met à jour une cellule (ligne, colonne).
    """
    sheet = get_sheet(name)
    sheet.update_cell(row, col, value)
