"""
Configuration centrale de l'API — remplace st.secrets.

Lit les variables depuis le fichier .env à la racine du projet.
Créer un .env local (non versionné) avec les valeurs ci-dessous.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Google Sheets
    sheet_id: str = ""
    gcp_service_account_json: str = ""   # contenu JSON du fichier de credentials, en une seule ligne

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7   # 7 jours

    # Brevo (email)
    brevo_api_key: str = ""
    brevo_sender: str = ""

    # IBU
    ibu_season_code: str = "2526"


@lru_cache
def get_settings() -> Settings:
    return Settings()
