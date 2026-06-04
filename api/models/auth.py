from pydantic import BaseModel, EmailStr


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
    password: str


class UserPublic(BaseModel):
    user_id: str
    username: str
    email: str


class ResetRequestBody(BaseModel):
    email: EmailStr


class ResetPasswordBody(BaseModel):
    email: EmailStr
    code: str
    new_password: str


class UpdateUsernameBody(BaseModel):
    new_username: str


class UpdatePasswordBody(BaseModel):
    old_password: str
    new_password: str


class FeedbackBody(BaseModel):
    feedback_type: str
    subject: str
    message: str
