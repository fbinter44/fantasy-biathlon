import hashlib
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import re
import secrets
import requests

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def validate_username(username: str) -> tuple[bool, str]:
    if not 3 <= len(username) <= 20:
        return False, "Le nom d'utilisateur doit contenir entre 3 et 20 caractères."

    if not re.match(r"^[A-Za-z0-9_]+$", username):
        return False, "Seules les lettres, chiffres et underscores (_) sont autorisés."

    return True, ""


def normalize_username(username: str) -> str:
    return username.strip().lower()


def validate_email(email: str) -> tuple[bool, str]:
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return False, "Adresse email invalide."
    return True, ""


def get_users_sheet():
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


def authenticate(identifier, password):
    identifier = identifier.strip().lower()
    password_hash = hash_password(password)

    sheet = get_users_sheet()
    users = sheet.get_all_records()

    for user in users:
        if identifier in (user["username"], user["email"]):
            if user["password_hash"] == password_hash:
                return True, user["username"]
            return False, "Mot de passe incorrect."

    return False, "Utilisateur introuvable."


def create_account(username, email, password):
    username = normalize_username(username)
    email = email.strip().lower()

    # Vérifications
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

    password_hash = hash_password(password)

    sheet.append_row([username, email, password_hash])
    return True, "Compte créé avec succès."


def generate_reset_code():
    return secrets.token_hex(3)  # ex: "a3f9c1"


def request_password_reset(email):
    email = email.strip().lower()
    sheet = get_users_sheet()
    users = sheet.get_all_records()

    for i, user in enumerate(users, start=2):
        if user["email"] == email:
            code = generate_reset_code()
            sheet.update_cell(i, 4, code)

            sent = send_reset_email(email, code)

            if sent:
                return True, "Un email contenant ton code a été envoyé."
            else:
                return False, "Erreur lors de l'envoi de l'email."

    return False, "Email introuvable."


def reset_password(email, code, new_password):
    email = email.strip().lower()
    sheet = get_users_sheet()
    users = sheet.get_all_records()

    for i, user in enumerate(users, start=2):
        if user["email"] == email:
            if user.get("reset_code") != code:
                return False, "Code incorrect."

            new_hash = hash_password(new_password)
            sheet.update_cell(i, 3, new_hash)  # password_hash
            sheet.update_cell(i, 4, "")  # reset_code effacé
            return True, "Mot de passe réinitialisé."

    return False, "Email introuvable."


def send_reset_email(to_email, code):
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
