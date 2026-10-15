"""
Routes d'authentification.

POST /auth/login          → TokenResponse
POST /auth/register       → UserPublic (compte non activé, email d'activation envoyé)
POST /auth/verify-email   → TokenResponse (active le compte et connecte)
POST /auth/resend-verification → message
POST /auth/reset-request  → message
POST /auth/reset-password → message
GET  /auth/me             → UserPublic
PATCH /auth/me/username   → UserPublic
PATCH /auth/me/password   → message
POST /auth/feedback       → message
"""

import secrets
import time
import uuid
import bcrypt

RESET_CODE_TTL = 15 * 60  # 15 minutes en secondes — doit correspondre à CODE_TTL côté frontend (app/reset-password/page.tsx)
VERIFY_TOKEN_TTL = 24 * 60 * 60  # 24 heures — mentionné dans le texte de l'email d'activation

# Détail renvoyé (403) par /login pour un compte non activé — le frontend s'appuie
# sur le statut 403 pour proposer le renvoi de l'email d'activation.
NOT_VERIFIED_DETAIL = "Ton compte n'est pas encore activé. Clique sur le lien reçu par email."

from fastapi import APIRouter, Depends, HTTPException, Request, status

from backend.config import Settings, get_settings
from backend.dependencies import create_access_token, get_current_user
from backend.models.auth import (
    LoginRequest, TokenResponse, RegisterRequest,
    VerifyEmailBody, ResendVerificationBody,
    ResetRequestBody, ResetPasswordBody, UserPublic,
    UpdateUsernameBody, UpdatePasswordBody, FeedbackBody,
)
from backend.rate_limit import limiter
from backend.services.db import (
    get_all_users, get_user_by_identifier, get_user_by_id,
    username_exists, email_exists,
    create_user, delete_user, delete_expired_unverified,
    get_user_by_verify_token, set_verify_token, mark_email_verified,
    update_user_field,
)
from backend.services.email import send_feedback_email, send_reset_email, send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# Hash factice utilisé quand l'utilisateur n'existe pas, pour que le login prenne
# le même temps que face à un mot de passe incorrect (évite l'énumération de
# comptes par mesure du temps de réponse).
_DUMMY_HASH = _hash("dummy-password-for-timing")


def _unique_id(existing: set, length: int = 8) -> str:
    while True:
        uid = str(uuid.uuid4())[:length]
        if uid not in existing:
            return uid


def _send_verification(email: str, username: str, token: str, settings: Settings) -> bool:
    link = f"{settings.frontend_url.rstrip('/')}/verify-email?token={token}"
    try:
        return send_verification_email(email, username, link, settings)
    except ValueError:
        return False


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest, settings: Settings = Depends(get_settings)):
    identifier = body.identifier.strip().lower()
    user = get_user_by_identifier(identifier, settings)
    # Toujours vérifier un hash (réel ou factice) pour que la réponse mette le
    # même temps que le compte existe ou non — message générique pour la même
    # raison, cf. _DUMMY_HASH ci-dessus.
    password_ok = _verify(body.password, user["password_hash"] if user else _DUMMY_HASH)
    if not user or not password_ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiant ou mot de passe incorrect.")
    # Vérifié après le mot de passe : seul le vrai propriétaire apprend que le
    # compte existe mais n'est pas activé.
    if not user["email_verified"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=NOT_VERIFIED_DETAIL)
    token = create_access_token(user["user_id"], settings)
    return TokenResponse(access_token=token, user_id=user["user_id"], username=user["username"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
def register(request: Request, body: RegisterRequest, settings: Settings = Depends(get_settings)):
    username = body.username.strip().lower()
    email = body.email.strip().lower()
    now = int(time.time())

    # Libère le username/email s'ils ne sont pris que par une inscription
    # jamais activée et dont le lien a expiré.
    delete_expired_unverified(username, email, now, settings)

    if username_exists(username, settings):
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur existe déjà.")
    if email_exists(email, settings):
        raise HTTPException(status_code=400, detail="Un compte existe déjà avec cet email.")

    users = get_all_users(settings)
    user_id = _unique_id({u["user_id"] for u in users})
    verify_token = secrets.token_urlsafe(32)
    create_user(user_id, username, email, _hash(body.password), verify_token, now + VERIFY_TOKEN_TTL, settings)

    if not _send_verification(email, username, verify_token, settings):
        # Sans email, le compte ne pourrait jamais être activé : on annule
        # l'inscription pour que l'utilisateur puisse réessayer.
        delete_user(user_id, settings)
        raise HTTPException(
            status_code=500,
            detail="L'email d'activation n'a pas pu être envoyé. Réessaie dans quelques minutes.",
        )
    return UserPublic(user_id=user_id, username=username, email=email)


@router.post("/verify-email", response_model=TokenResponse)
@limiter.limit("10/15minutes")
def verify_email(request: Request, body: VerifyEmailBody, settings: Settings = Depends(get_settings)):
    user = get_user_by_verify_token(body.token, settings) if body.token else None
    if not user:
        raise HTTPException(status_code=400, detail="Ce lien d'activation est invalide ou a déjà été utilisé.")
    if int(time.time()) > user["verify_expires"]:
        raise HTTPException(
            status_code=400,
            detail="Ce lien d'activation a expiré. Connecte-toi pour en recevoir un nouveau.",
        )
    mark_email_verified(user["user_id"], settings)
    token = create_access_token(user["user_id"], settings)
    return TokenResponse(access_token=token, user_id=user["user_id"], username=user["username"])


@router.post("/resend-verification")
@limiter.limit("3/15minutes")
def resend_verification(request: Request, body: ResendVerificationBody, settings: Settings = Depends(get_settings)):
    user = get_user_by_identifier(body.identifier.strip().lower(), settings)
    # Réponse identique que le compte existe ou non (pas d'énumération).
    if user and not user["email_verified"]:
        verify_token = secrets.token_urlsafe(32)
        set_verify_token(user["user_id"], verify_token, int(time.time()) + VERIFY_TOKEN_TTL, settings)
        if not _send_verification(user["email"], user["username"], verify_token, settings):
            raise HTTPException(
                status_code=500,
                detail="L'email d'activation n'a pas pu être envoyé. Réessaie dans quelques minutes.",
            )
    return {"detail": "Si ce compte attend une activation, un nouvel email vient d'être envoyé."}


@router.post("/reset-request")
@limiter.limit("3/15minutes")
def reset_request(request: Request, body: ResetRequestBody, settings: Settings = Depends(get_settings)):
    email = body.email.strip().lower()
    users = get_all_users(settings)
    user = next((u for u in users if u["email"] == email), None)
    if not user:
        raise HTTPException(status_code=404, detail="Email introuvable.")
    code = secrets.token_hex(3)
    expires_at = int(time.time()) + RESET_CODE_TTL
    update_user_field(user["user_id"], "reset_code", f"{code}|{expires_at}", settings)
    try:
        ok = send_reset_email(email, code, settings)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if not ok:
        raise HTTPException(
            status_code=500,
            detail="L'email n'a pas pu être envoyé. Vérifie les logs du backend (Brevo).",
        )
    return {"detail": "Un email contenant ton code a été envoyé."}


@router.post("/reset-password")
@limiter.limit("10/15minutes")
def reset_password(request: Request, body: ResetPasswordBody, settings: Settings = Depends(get_settings)):
    email = body.email.strip().lower()
    users = get_all_users(settings)
    user = next((u for u in users if u["email"] == email), None)
    if not user:
        raise HTTPException(status_code=404, detail="Email introuvable.")
    stored = user.get("reset_code") or ""
    # Format attendu : "a1b2c3|1725792000"
    parts = stored.split("|")
    if len(parts) != 2 or parts[0] != body.code:
        raise HTTPException(status_code=400, detail="Code incorrect.")
    if int(time.time()) > int(parts[1]):
        raise HTTPException(status_code=400, detail="Ce code a expiré. Recommence la procédure.")
    update_user_field(user["user_id"], "password_hash", _hash(body.new_password), settings)
    update_user_field(user["user_id"], "reset_code", "", settings)
    # Le code reçu par email prouve la possession de l'adresse : vaut activation.
    if not user["email_verified"]:
        mark_email_verified(user["user_id"], settings)
    return {"detail": "Mot de passe réinitialisé."}


@router.get("/me", response_model=UserPublic)
def get_me(current_user: str = Depends(get_current_user), settings: Settings = Depends(get_settings)):
    user = get_user_by_id(current_user, settings)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    return UserPublic(user_id=user["user_id"], username=user["username"], email=user["email"])


@router.patch("/me/username", response_model=UserPublic)
def update_username(
    body: UpdateUsernameBody,
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    new_username = body.new_username.strip().lower()
    if not new_username:
        raise HTTPException(status_code=400, detail="Le nom d'utilisateur ne peut pas être vide.")
    user = get_user_by_id(current_user, settings)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    existing = get_user_by_identifier(new_username, settings)
    if existing and existing["user_id"] != current_user:
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur est déjà utilisé.")
    update_user_field(current_user, "username", new_username, settings)
    return UserPublic(user_id=user["user_id"], username=new_username, email=user["email"])


@router.patch("/me/password")
def update_password(
    body: UpdatePasswordBody,
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    user = get_user_by_id(current_user, settings)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
    if not _verify(body.old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Ancien mot de passe incorrect.")
    update_user_field(current_user, "password_hash", _hash(body.new_password), settings)
    return {"detail": "Mot de passe mis à jour avec succès."}


@router.post("/feedback")
def send_feedback(
    body: FeedbackBody,
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
):
    user = get_user_by_id(current_user, settings)
    username = user["username"] if user else current_user

    try:
        ok = send_feedback_email(username, body.feedback_type, body.subject, body.message, settings)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if not ok:
        raise HTTPException(
            status_code=500,
            detail="Le feedback n'a pas pu être envoyé. Vérifie les logs du backend (Brevo).",
        )
    return {"detail": "Merci pour ton feedback !"}
