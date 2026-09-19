"""
Envoi d'emails via Brevo (anciennement Sendinblue).
"""

import logging
import requests
from backend.config import Settings

logger = logging.getLogger(__name__)

BREVO_URL = "https://api.brevo.com/v3/smtp/email"


def _require_brevo_config(settings: Settings) -> None:
    if not settings.brevo_api_key:
        raise ValueError("BREVO_API_KEY non configurée dans les variables d'environnement.")
    if not settings.brevo_sender:
        raise ValueError("BREVO_SENDER non configuré dans les variables d'environnement.")


def _send_brevo_email(payload: dict, settings: Settings, *, log_context: str) -> bool:
    """
    Envoie un email via l'API Brevo. Retourne True si succès, False + log en cas
    d'échec (réseau, timeout, ou statut d'erreur Brevo).
    """
    headers = {
        "api-key": settings.brevo_api_key,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(BREVO_URL, json=payload, headers=headers, timeout=10)
    except requests.exceptions.RequestException as exc:
        logger.error("Brevo — erreur réseau (%s) : %s", log_context, exc)
        return False

    if response.status_code == 201:
        return True

    # Log détaillé pour faciliter le diagnostic
    try:
        detail = response.json()
    except Exception:
        detail = response.text

    logger.error("Brevo — statut %s (%s) : %s", response.status_code, log_context, detail)
    return False


def send_reset_email(to_email: str, code: str, settings: Settings) -> bool:
    """
    Envoie le code de réinitialisation par email via l'API Brevo.
    Retourne True si succès, False + log en cas d'échec.
    Lève une ValueError avec le message Brevo si la clé ou le sender manquent.
    """
    _require_brevo_config(settings)

    payload = {
        "sender": {"name": "Clean Shot", "email": settings.brevo_sender},
        "to": [{"email": to_email}],
        "subject": "Réinitialisation de ton mot de passe — Clean Shot",
        "textContent": (
            "Bonjour,\n\n"
            f"Voici ton code de réinitialisation : {code}\n\n"
            "Entre ce code dans l'application pour choisir un nouveau mot de passe.\n\n"
            "Le code est valable 15 minutes et à usage unique.\n\n"
            "Si tu n'es pas à l'origine de cette demande, ignore simplement cet email.\n\n"
            "À bientôt sur Clean Shot !\n"
            "— L'équipe Clean Shot\n\n"
            "---\n"
            "Clean Shot · clean-shot.app\n"
            "Pour toute question : support@clean-shot.app"
        ),
    }
    return _send_brevo_email(payload, settings, log_context=f"reset pour {to_email}")


def send_feedback_email(username: str, feedback_type: str, subject: str, message: str, settings: Settings) -> bool:
    """
    Envoie un feedback utilisateur à l'adresse de contact (BREVO_SENDER), via Brevo.
    Retourne True si succès, False + log en cas d'échec.
    Lève une ValueError si la clé ou le sender manquent.
    """
    _require_brevo_config(settings)

    payload = {
        "sender": {"name": "Clean Shot", "email": settings.brevo_sender},
        "to": [{"email": settings.brevo_sender}],
        "subject": f"[Feedback Clean Shot] {feedback_type} — {subject}",
        "textContent": f"De : {username}\nType : {feedback_type}\n\n{message}",
    }
    return _send_brevo_email(payload, settings, log_context=f"feedback de {username}")
