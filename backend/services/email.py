"""
Envoi d'emails via Brevo (anciennement Sendinblue).
"""

import logging
import requests
from backend.config import Settings

logger = logging.getLogger(__name__)


def send_reset_email(to_email: str, code: str, settings: Settings) -> bool:
    """
    Envoie le code de réinitialisation par email via l'API Brevo.
    Retourne True si succès, False + log en cas d'échec.
    Lève une ValueError avec le message Brevo si la clé ou le sender manquent.
    """
    if not settings.brevo_api_key:
        raise ValueError("BREVO_API_KEY non configurée dans les variables d'environnement.")
    if not settings.brevo_sender:
        raise ValueError("BREVO_SENDER non configuré dans les variables d'environnement.")

    url = "https://api.brevo.com/v3/smtp/email"
    payload = {
        "sender": {"name": "Clean Shot", "email": settings.brevo_sender},
        "to": [{"email": to_email}],
        "subject": "Réinitialisation de ton mot de passe — Clean Shot",
        "textContent": (
            "Bonjour,\n\n"
            f"Voici ton code de réinitialisation : {code}\n\n"
            "Entre ce code dans l'application pour choisir un nouveau mot de passe.\n\n"
            "Le code est à usage unique.\n\n"
            "À bientôt sur Clean Shot !"
        ),
    }
    headers = {
        "api-key": settings.brevo_api_key,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
    except requests.exceptions.RequestException as exc:
        logger.error("Brevo — erreur réseau : %s", exc)
        return False

    if response.status_code == 201:
        return True

    # Log détaillé pour faciliter le diagnostic
    try:
        detail = response.json()
    except Exception:
        detail = response.text

    logger.error(
        "Brevo — statut %s pour %s : %s",
        response.status_code,
        to_email,
        detail,
    )
    return False
