"""
Accès Google Sheets sans st.secrets.

Remplace utils/sheets.py pour l'API FastAPI.
Reçoit les credentials depuis api/config.py (env vars).
"""

import json
import time
import gspread
from google.oauth2.service_account import Credentials

from backend.config import Settings


_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Cache en mémoire : { sheet_name → (data, expires_at) }
_cache: dict[str, tuple[list[dict], float]] = {}

# TTL par feuille (secondes)
_TTL: dict[str, int] = {
    "Pronostics": 300,   # 5 min — ne change qu'avant la deadline
    "Leagues":    120,   # 2 min
    "Users":       60,   # 1 min
}
_DEFAULT_TTL = 60


def _get_client(settings: Settings) -> gspread.Client:
    creds_dict = json.loads(settings.gcp_service_account_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=_SCOPES)
    return gspread.authorize(creds)


def get_sheet(name: str, settings: Settings) -> gspread.Worksheet:
    client = _get_client(settings)
    return client.open_by_key(settings.sheet_id).worksheet(name)


def read_all(name: str, settings: Settings) -> list[dict]:
    now = time.monotonic()
    if name in _cache:
        data, expires_at = _cache[name]
        if now < expires_at:
            return data

    data = get_sheet(name, settings).get_all_records()
    ttl = _TTL.get(name, _DEFAULT_TTL)
    _cache[name] = (data, now + ttl)
    return data


def _invalidate(name: str) -> None:
    _cache.pop(name, None)


def append_row(name: str, row: list, settings: Settings) -> None:
    get_sheet(name, settings).append_row(row)
    _invalidate(name)


def update_cell(name: str, row: int, col: int, value, settings: Settings) -> None:
    get_sheet(name, settings).update_cell(row, col, value)
    _invalidate(name)


def delete_row(name: str, row: int, settings: Settings) -> None:
    get_sheet(name, settings).delete_rows(row)
    _invalidate(name)
