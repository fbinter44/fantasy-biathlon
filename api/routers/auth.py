"""
Routes d'authentification.

POST /auth/login     → TokenResponse
POST /auth/register  → UserPublic
POST /auth/reset-request  → message
POST /auth/reset-password → message
"""

import secrets
import uuid
import bcrypt

from fastapi import APIRouter, Depends, HTTPException, status

from api.config import Settings, get_settings
from api.dependencies import create_access_token
from api.models.auth import (
    LoginRequest, TokenResponse, RegisterRequest,
    ResetRequestBody, ResetPasswordBody, UserPublic,
)
from api.services.sheets import read_all, get_sheet, append_row, update_cell
from api.services.email import send_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------
# helpers
# ---------------------------------------------------------

def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def _unique_id(existing: set, length: int = 8) -> str:
    while True:
        uid = str(uuid.uuid4())[:length]
        if uid not in existing:
            return uid


# ---------------------------------------------------------
# routes
# ---------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, settings: Settings = Depends(get_settings)):
    identifier = body.identifier.strip().lower()
    users = read_all("Users", settings)

    for user in users:
        if identifier in (user["username"], user["email"]):
            if not _verify(body.password, user["password_hash"]):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Mot de passe incorrect.")
            token = create_access_token(user["user_id"], settings)
            return TokenResponse(
                access_token=token,
                user_id=user["user_id"],
                username=user["username"],
            )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable.")


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, settings: Settings = Depends(get_settings)):
    username = body.username.strip().lower()
    email = body.email.strip().lower()
    users = read_all("Users", settings)

    if any(u["username"] == username for u in users):
        raise HTTPException(status_code=400, detail="Ce nom d'utilisateur existe déjà.")
    if any(u["email"] == email for u in users):
        raise HTTPException(status_code=400, detail="Un compte existe déjà avec cet email.")

    user_id = _unique_id({u["user_id"] for u in users})
    password_hash = _hash(body.password)
    append_row("Users", [username, user_id, email, password_hash], settings)

    return UserPublic(user_id=user_id, username=username, email=email)


@router.post("/reset-request")
def reset_request(body: ResetRequestBody, settings: Settings = Depends(get_settings)):
    email = body.email.strip().lower()
    sheet = get_sheet("Users", settings)
    users = sheet.get_all_records()

    for i, user in enumerate(users, start=2):
        if user["email"] == email:
            code = secrets.token_hex(3)
            update_cell("Users", i, 5, code, settings)
            sent = send_reset_email(email, code, settings)
            if not sent:
                raise HTTPException(status_code=500, detail="Erreur lors de l'envoi de l'email.")
            return {"detail": "Un email contenant ton code a été envoyé."}

    raise HTTPException(status_code=404, detail="Email introuvable.")


@router.post("/reset-password")
def reset_password(body: ResetPasswordBody, settings: Settings = Depends(get_settings)):
    email = body.email.strip().lower()
    sheet = get_sheet("Users", settings)
    users = sheet.get_all_records()

    for i, user in enumerate(users, start=2):
        if user["email"] == email:
            if user.get("reset_code") != body.code:
                raise HTTPException(status_code=400, detail="Code incorrect.")
            update_cell("Users", i, 4, _hash(body.new_password), settings)
            update_cell("Users", i, 5, "", settings)
            return {"detail": "Mot de passe réinitialisé."}

    raise HTTPException(status_code=404, detail="Email introuvable.")
