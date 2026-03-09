"""
Module d'authentification de l'application.

Responsabilités :
- Gestion des mots de passe (hash + vérification)
- Validation des identifiants (username / email)
- Connexion utilisateur
- Création de compte
- Gestion du reset password (génération + vérification)
- Communication avec Google Sheets (feuille Users)
- Envoi d'email via Brevo

Ce module ne contient AUCUNE logique Streamlit (UI).
"""

import re
import secrets
import json
import bcrypt
import requests
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st


# ---------------------------------------------------------
# 1) GESTION DES MOTS DE PASSE
# ---------------------------------------------------------

def hash_password(password: str) -> str:
    """Retourne un hash bcrypt sécurisé pour un mot de passe."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Vérifie qu'un mot de passe correspond à un hash bcrypt."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ---------------------------------------------------------
# 2) VALIDATION DES IDENTIFIANTS
# ---------------------------------------------------------

def validate_username(username: str) -> tuple[bool, str]:
    """Vérifie que le username est conforme aux règles."""
    if not 3 <= len(username) <= 20:
        return False, "Le nom d'utilisateur doit contenir entre 3 et 20 caractères."

    if not re.match(r"^[A-Za-z0-9_]+$", username):
        return False, "Seules les lettres, chiffres et underscores (_) sont autorisés."

    return True, ""


def normalize_username(username: str) -> str:
    """Normalise un username (trim + lowercase)."""
    return username.strip().lower()


def validate_email(email: str) -> tuple[bool, str]:
    """Vérifie que l'email a un format valide."""
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return False, "Adresse email invalide."
    return True, ""


# ---------------------------------------------------------
# 3) ACCÈS À GOOGLE SHEETS
# ---------------------------------------------------------

def get_users_sheet():
    """Retourne la feuille Google Sheets 'Users'."""
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    client = gspread.authorize(creds)
    return client.open_by_key(st.secrets["sheets"]["sheet_id"]).worksheet("Users")


# ---------------------------------------------------------
# 4) AUTHENTIFICATION
# ---------------------------------------------------------

def authenticate(identifier: str, password: str):
    """
    Authentifie un utilisateur via username OU email.
    Retourne (True, username) si OK, sinon (False, message d'erreur).
    """
    identifier = identifier.strip().lower()

    sheet = get_users_sheet()
    users = sheet.get_all_records()

    for user in users:
        if identifier in (user["username"], user["email"]):
            if verify_password(password, user["password_hash"]):
                return True, user["username"]
            return False, "Mot de passe incorrect."

    return False, "Utilisateur introuvable."


# ---------------------------------------------------------
# 5) CRÉATION DE COMPTE
# ---------------------------------------------------------

def create_account(username: str, email: str, password: str):
    """
    Crée un nouveau compte utilisateur si :
    - username valide et unique
    - email valide et unique
    - mot de passe fourni
    """
    username = normalize_username(username)
    email = email.strip().lower()

    # Validation des champs
    ok, msg = validate_username(username)
    if not ok:
        return False, msg

    ok, msg = validate_email(email)
    if not ok:
        return False, msg

    sheet = get_users_sheet()
    users = sheet.get_all_records()

    # Unicité username
    if any(u["username"] == username for u in users):
        return False, "Ce nom d'utilisateur existe déjà."

    # Unicité email
    if any(u["email"] == email for u in users):
        return False, "Un compte existe déjà avec cet email."

    # Hash du mot de passe
    password_hash = hash_password(password)

    # Ajout dans Google Sheets
    sheet.append_row([username, email, password_hash])

    return True, "Compte créé avec succès."


# ---------------------------------------------------------
# 6) RESET PASSWORD
# ---------------------------------------------------------

def generate_reset_code() -> str:
    """Génère un code court et aléatoire pour le reset password."""
    return secrets.token_hex(3)  # ex: "a3f9c1"


def request_password_reset(email: str):
    """
    Génère un code de reset et l'envoie par email.
    Retourne (True, message) ou (False, erreur).
    """
    email = email.strip().lower()
    sheet = get_users_sheet()
    users = sheet.get_all_records()

    for i, user in enumerate(users, start=2):  # ligne 2 = première ligne de données
        if user["email"] == email:
            code = generate_reset_code()

            # Colonne 4 = reset_code
            sheet.update_cell(i, 4, code)

            sent = send_reset_email(email, code)
            if sent:
                return True, "Un email contenant ton code a été envoyé."
            return False, "Erreur lors de l'envoi de l'email."

    return False, "Email introuvable."


def reset_password(email: str, code: str, new_password: str):
    """
    Réinitialise le mot de passe si le code est correct.
    """
    email = email.strip().lower()
    sheet = get_users_sheet()
    users = sheet.get_all_records()

    for i, user in enumerate(users, start=2):
        if user["email"] == email:

            if user.get("reset_code") != code:
                return False, "Code incorrect."

            new_hash = hash_password(new_password)

            sheet.update_cell(i, 3, new_hash)  # Colonne 3 = password_hash
            sheet.update_cell(i, 4, "")        # Colonne 4 = reset_code (effacé)

            return True, "Mot de passe réinitialisé."

    return False, "Email introuvable."


# ---------------------------------------------------------
# 7) ENVOI D'EMAIL (BREVO)
# ---------------------------------------------------------

def send_reset_email(to_email: str, code: str) -> bool:
    """Envoie un email contenant le code de réinitialisation."""
    api_key = st.secrets["brevo"]["api_key"]
    sender = st.secrets["brevo"]["sender"]

    url = "https://api.brevo.com/v3/smtp/email"

    data = {
        "sender": {"email": sender},
        "to": [{"email": to_email}],
        "subject": "Réinitialisation de ton mot de passe",
        "textContent": (
            "Bonjour,\n\n"
            f"Voici ton code de réinitialisation : {code}\n\n"
            "Entre ce code dans l'application pour choisir un nouveau mot de passe.\n\n"
            "À bientôt !"
        )
    }

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=data, headers=headers)
    return response.status_code == 201
