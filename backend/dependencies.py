"""
Dépendances FastAPI partagées entre les routers.

- get_settings : injection de la configuration
- get_current_user : vérifie le JWT et retourne l'user_id
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

from backend.config import Settings, get_settings
from backend.services.db import get_user_by_id

_bearer = HTTPBearer()


# ---------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------

def create_access_token(user_id: str, settings: Settings) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> str:
    """Retourne l'user_id extrait du JWT, ou lève 401."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception


def require_admin(
    current_user: str = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> str:
    """Comme get_current_user, mais exige que le compte fasse partie de
    ADMIN_USERNAMES (voir backend/config.py). Pas de rôle en base — juste une
    liste de usernames en config, vérifiée sur le compte JWT déjà connecté."""
    admins = {u.strip().lower() for u in settings.admin_usernames.split(",") if u.strip()}
    user = get_user_by_id(current_user, settings)
    if not user or user["username"].lower() not in admins:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Réservé aux administrateurs.")
    return current_user
