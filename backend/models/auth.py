from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr
from pydantic_core import PydanticCustomError


def _check_password_length(v: str) -> str:
    # PydanticCustomError plutôt que ValueError : évite le préfixe anglais
    # "Value error, " que Pydantic ajoute automatiquement autour d'un ValueError.
    if len(v) < 6:
        raise PydanticCustomError(
            "password_too_short",
            "Le mot de passe doit contenir au moins 6 caractères.",
        )
    return v


Password = Annotated[str, AfterValidator(_check_password_length)]


class LoginRequest(BaseModel):
    identifier: str   # username ou email
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: Password


class UserPublic(BaseModel):
    user_id: str
    username: str
    email: str


class ResetRequestBody(BaseModel):
    email: EmailStr


class ResetPasswordBody(BaseModel):
    email: EmailStr
    code: str
    new_password: Password


class UpdateUsernameBody(BaseModel):
    new_username: str


class UpdatePasswordBody(BaseModel):
    old_password: str
    new_password: Password


class FeedbackBody(BaseModel):
    feedback_type: str
    subject: str
    message: str
