"""
Module d'authentification de l'application.

Responsabilités :
- Gestion des mots de passe (hash + vérification)
- Validation des identifiants (username / email)
- Connexion utilisateur
- Création de compte
- Gestion du reset password (génération + vérification)
- Envoi d'email via Brevo

Toute la communication avec Google Sheets passe par utils.sheets.
"""

import re
import secrets
import bcrypt
import requests
import streamlit as st
import uuid
import random
import string

from utils.sheets import get_sheet, append_row, update_cell, read_all


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
# 3) AUTHENTIFICATION
# ---------------------------------------------------------

def authenticate(identifier: str, password: str):
    """
    Authentifie un utilisateur via username OU email.
    Retourne (True, username) si OK, sinon (False, message d'erreur).
    """
    identifier = identifier.strip().lower()

    sheet = get_sheet("Users")
    users = sheet.get_all_records()

    for user in users:
        if identifier in (user["username"], user["email"]):
            if verify_password(password, user["password_hash"]):
                return True, user["user_id"]
            return False, "Mot de passe incorrect."

    return False, "Utilisateur introuvable."


def convert_id_to_name(user_id):
    if not user_id:
        return None
    users = read_all("Users")
    id_to_name = {u["user_id"]: u["username"] for u in users}
    return id_to_name[user_id]

def convert_league_id_to_name(league_id):
    if not league_id:
        return None
    leagues = read_all("Leagues")
    id_to_name = {l["league_id"]: l["league_name"] for l in leagues}
    return id_to_name[league_id]


def get_mapping_id_to_name():
    users = read_all("Users")
    return {u["user_id"]: u["username"] for u in users}


def get_mapping_league_id_to_name():
    leagues = read_all("Leagues")
    return {l["league_id"]: l["league_name"] for l in leagues}


# ---------------------------------------------------------
# 4) CRÉATION DE COMPTE
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

    sheet = get_sheet("Users")
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
    existing_ids = {row["user_id"] for row in users}
    user_id = generate_unique_user_id(existing_ids)
    append_row("Users", [username, user_id, email, password_hash])

    return True, "Compte créé avec succès."


def generate_unique_user_id(existing_ids):
    while True:
        user_id = str(uuid.uuid4())[:8]
        if user_id not in existing_ids:
            return user_id


# ---------------------------------------------------------
# 5) RESET PASSWORD
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
    sheet = get_sheet("Users")
    users = sheet.get_all_records()

    for i, user in enumerate(users, start=2):  # ligne 2 = première ligne de données
        if user["email"] == email:
            code = generate_reset_code()

            # Colonne 4 = reset_code
            update_cell("Users", i, 5, code)

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
    sheet = get_sheet("Users")
    users = sheet.get_all_records()

    for i, user in enumerate(users, start=2):
        if user["email"] == email:

            if user.get("reset_code") != code:
                return False, "Code incorrect."

            new_hash = hash_password(new_password)

            update_cell("Users", i, 4, new_hash)  # Colonne 3 = password_hash
            update_cell("Users", i, 5, "")        # Colonne 4 = reset_code (effacé)

            return True, "Mot de passe réinitialisé."

    return False, "Email introuvable."


# ---------------------------------------------------------
# 6) ENVOI D'EMAIL (BREVO)
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


# ---------------------------------------------------------
# 7) GESTION DES LIGUES
# ---------------------------------------------------------

def generate_unique_invite_code(length=6):
    chars = string.ascii_uppercase + string.digits

    leagues = read_all("Leagues")
    existing_codes = {lg.get("invite_code") for lg in leagues if lg.get("invite_code")}

    while True:
        code = ''.join(random.choice(chars) for _ in range(length))
        if code not in existing_codes:
            return code
