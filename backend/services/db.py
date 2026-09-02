"""
Service base de données PostgreSQL — remplace api/services/sheets.py.

Utilise psycopg2 avec un pool de connexions. La pool est initialisée
une seule fois (singleton) à partir de settings.database_url.
"""

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from backend.config import Settings

_pool: ThreadedConnectionPool | None = None


def _get_pool(settings: Settings) -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        dsn = settings.database_url
        if "sslmode" not in dsn:
            dsn += "?sslmode=require"
        _pool = ThreadedConnectionPool(1, 10, dsn)
    return _pool


@contextmanager
def _conn(settings: Settings):
    pool = _get_pool(settings)
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


# ─── Users ────────────────────────────────────────────────────────────────────

def get_all_users(settings: Settings) -> list[dict]:
    with _conn(settings) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT user_id, username, email, password_hash, reset_code FROM users")
            return [dict(r) for r in cur.fetchall()]


def get_user_by_id(user_id: str, settings: Settings) -> dict | None:
    with _conn(settings) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def get_user_by_identifier(identifier: str, settings: Settings) -> dict | None:
    """Recherche par username ou email (insensible à la casse)."""
    with _conn(settings) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM users WHERE LOWER(username) = %s OR LOWER(email) = %s",
                (identifier, identifier),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def username_exists(username: str, settings: Settings) -> bool:
    with _conn(settings) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE LOWER(username) = %s", (username.lower(),))
            return cur.fetchone() is not None


def email_exists(email: str, settings: Settings) -> bool:
    with _conn(settings) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE LOWER(email) = %s", (email.lower(),))
            return cur.fetchone() is not None


def create_user(user_id: str, username: str, email: str, password_hash: str, settings: Settings) -> None:
    with _conn(settings) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (user_id, username, email, password_hash) VALUES (%s, %s, %s, %s)",
                (user_id, username, email, password_hash),
            )


def update_user_field(user_id: str, field: str, value: str, settings: Settings) -> None:
    _ALLOWED_USER_FIELDS = {"username", "password_hash", "reset_code"}
    if field not in _ALLOWED_USER_FIELDS:
        raise ValueError(f"Champ non autorisé : {field}")
    with _conn(settings) as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE users SET {field} = %s WHERE user_id = %s", (value, user_id))


# ─── Pronostics ───────────────────────────────────────────────────────────────

def get_all_pronostics(settings: Settings, season: str) -> list[dict]:
    with _conn(settings) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM pronostics WHERE season = %s", (season,))
            return [dict(r) for r in cur.fetchall()]


def get_pronostics_by_user(user_id: str, settings: Settings, season: str) -> dict | None:
    with _conn(settings) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM pronostics WHERE user_id = %s AND season = %s",
                (user_id, season),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def upsert_pronostics(user_id: str, settings: Settings, season: str, **kwargs) -> None:
    """Crée la ligne si absente, sinon met à jour uniquement les champs fournis."""
    _ALLOWED = {
        "top5_h", "top5_f",
        "globe_sprint_h", "globe_sprint_f",
        "globe_pursuit_h", "globe_pursuit_f",
        "globe_individual_h", "globe_individual_f",
        "globe_mass_start_h", "globe_mass_start_f",
    }
    fields = {k: v for k, v in kwargs.items() if k in _ALLOWED}
    if not fields:
        return

    cols = list(fields.keys())
    vals = [fields[c] for c in cols]
    placeholders = ", ".join(["%s"] * len(cols))
    updates = ", ".join([f"{c} = EXCLUDED.{c}" for c in cols])

    sql = f"""
        INSERT INTO pronostics (user_id, season, {", ".join(cols)})
        VALUES (%s, %s, {placeholders})
        ON CONFLICT (user_id, season) DO UPDATE SET {updates}
    """
    with _conn(settings) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, [user_id, season] + vals)


# ─── Leagues ──────────────────────────────────────────────────────────────────

def get_all_leagues(settings: Settings) -> list[dict]:
    with _conn(settings) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM leagues")
            return [dict(r) for r in cur.fetchall()]


def get_league_by_id(league_id: str, settings: Settings) -> dict | None:
    with _conn(settings) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM leagues WHERE league_id = %s", (league_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def get_league_by_invite_code(code: str, settings: Settings) -> dict | None:
    with _conn(settings) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM leagues WHERE invite_code = %s", (code,))
            row = cur.fetchone()
            return dict(row) if row else None


def create_league(
    league_id: str, name: str, owner: str, members: str, invite_code: str, settings: Settings
) -> None:
    with _conn(settings) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO leagues (league_id, league_name, owner, members, invite_code) VALUES (%s, %s, %s, %s, %s)",
                (league_id, name, owner, members, invite_code),
            )


def update_league_members(league_id: str, members_str: str, settings: Settings) -> None:
    with _conn(settings) as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE leagues SET members = %s WHERE league_id = %s", (members_str, league_id))


def delete_league_by_id(league_id: str, settings: Settings) -> None:
    with _conn(settings) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM leagues WHERE league_id = %s", (league_id,))


# ─── Race pronostics ──────────────────────────────────────────────────────────

def get_all_race_pronostics(settings: Settings, season: str) -> dict:
    """Retourne {user_id: {race_id: ibu_id}} pour tous les utilisateurs."""
    with _conn(settings) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT user_id, race_id, ibu_id FROM race_pronostics WHERE season = %s",
                (season,),
            )
            result: dict = {}
            for row in cur.fetchall():
                result.setdefault(row["user_id"], {})[row["race_id"]] = row["ibu_id"]
            return result


def get_race_pronostics_by_user(user_id: str, settings: Settings, season: str) -> dict:
    """Retourne {race_id: ibu_id} pour tous les pronos course de l'utilisateur."""
    with _conn(settings) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT race_id, ibu_id FROM race_pronostics WHERE user_id = %s AND season = %s",
                (user_id, season),
            )
            return {row["race_id"]: row["ibu_id"] for row in cur.fetchall()}


def upsert_race_pronostic(
    user_id: str, race_id: str, ibu_id: str, settings: Settings, season: str
) -> None:
    """Crée ou met à jour le pronostic vainqueur d'une course."""
    with _conn(settings) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO race_pronostics (user_id, race_id, ibu_id, season)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, race_id, season) DO UPDATE SET ibu_id = EXCLUDED.ibu_id
                """,
                (user_id, race_id, ibu_id, season),
            )


def delete_race_pronostic(user_id: str, race_id: str, settings: Settings, season: str) -> None:
    with _conn(settings) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM race_pronostics WHERE user_id = %s AND race_id = %s AND season = %s",
                (user_id, race_id, season),
            )
