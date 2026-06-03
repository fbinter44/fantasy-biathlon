"""
Accès Google Sheets sans st.secrets.

Remplace utils/sheets.py pour l'API FastAPI.
Reçoit les credentials depuis api/config.py (env vars).
"""

import json
import gspread
from google.oauth2.service_account import Credentials
from functools import lru_cache

from api.config import Settings


_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _get_client(settings: Settings) -> gspread.Client:
    creds_dict = json.loads(settings.gcp_service_account_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=_SCOPES)
    return gspread.authorize(creds)


def get_sheet(name: str, settings: Settings) -> gspread.Worksheet:
    client = _get_client(settings)
    return client.open_by_key(settings.sheet_id).worksheet(name)


def read_all(name: str, settings: Settings) -> list[dict]:
    return get_sheet(name, settings).get_all_records()


def append_row(name: str, row: list, settings: Settings) -> None:
    get_sheet(name, settings).append_row(row)


def update_cell(name: str, row: int, col: int, value, settings: Settings) -> None:
    get_sheet(name, settings).update_cell(row, col, value)
