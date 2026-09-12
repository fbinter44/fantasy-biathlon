"""
Configuration centrale de l'API — remplace st.secrets.

Lit les variables depuis le fichier .env à la racine du projet.
Créer un .env local (non versionné) avec les valeurs ci-dessous.
"""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

from utils.biathlon_data import current_ibu_season_code


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # PostgreSQL
    database_url: str = ""

    # JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7   # 7 jours

    # Brevo (email)
    brevo_api_key: str = ""
    brevo_sender: str = ""

    # IBU — vide = calculée automatiquement depuis la date (bascule le 1er nov.).
    # Ne renseigner IBU_SEASON_CODE dans .env / Railway que pour forcer une
    # saison précise (tests, rollback d'urgence) : ça désactive l'auto-bascule.
    ibu_season_code: str = ""

    @model_validator(mode="after")
    def _resolve_season_code(self) -> "Settings":
        if not self.ibu_season_code:
            self.ibu_season_code = current_ibu_season_code()
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
