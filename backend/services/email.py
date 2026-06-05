"""
Envoi d'emails via Brevo sans st.secrets.
"""

import requests
from backend.config import Settings


def send_reset_email(to_email: str, code: str, settings: Settings) -> bool:
    url = "https://api.brevo.com/v3/smtp/email"
    data = {
        "sender": {"email": settings.brevo_sender},
        "to": [{"email": to_email}],
        "subject": "Réinitialisation de ton mot de passe",
        "textContent": (
            "Bonjour,\n\n"
            f"Voici ton code de réinitialisation : {code}\n\n"
            "Entre ce code dans l'application pour choisir un nouveau mot de passe.\n\n"
            "À bientôt !"
        ),
    }
    headers = {"api-key": settings.brevo_api_key, "Content-Type": "application/json"}
    response = requests.post(url, json=data, headers=headers)
    return response.status_code == 201
