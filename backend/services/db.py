"""
Service base de données PostgreSQL — remplace api/services/sheets.py.

Utilise psycopg2 avec un pool de connexions. La pool est initialisée
une seule fois (singleton) à partir de settings.database_url.
"""

import time

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from backend.config import Settings

_pool: ThreadedConnectionPool | None = None

# Une connexion restée inactive plus longtemps est jetée plutôt que réutilisée :
# en prod, le réseau entre Railway et Supabase coupe silencieusement les
# connexions inactives, et la requête suivante plantait ("Connection timed out").
_MAX_IDLE_SECONDS = 60
_last_used: dict[int, float] = {}  # id(conn) → dernier retour dans la pool


def _get_pool(settings: Settings) -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        dsn = settings.database_url
        if "sslmode" not in dsn:
            dsn += "?sslmode=require"
        _pool = ThreadedConnectionPool(
            1, 10, dsn,
            connect_timeout=10,
            # Keepalives TCP : maintiennent la connexion ouverte et détectent vite une coupure.
            keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3,
        )
    return _pool


def _checkout(pool: ThreadedConnectionPool):
    """Prend une connexion saine dans la pool, en jetant les fermées ou trop longtemps inactives."""
    while True:
        conn = pool.getconn()
        last_used = _last_used.pop(id(conn), None)
        if not conn.closed and (last_used is None or time.monotonic() - last_used < _MAX_IDLE_SECONDS):
            return conn
        pool.putconn(conn, close=True)


@contextmanager
def _conn(settings: Settings):
    pool = _get_pool(settings)
    conn = _checkout(pool)
    broken = False
    try:
        yield conn
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except psycopg2.Error:
            broken = True
        raise
    finally:
        # Une connexion cassée est fermée au lieu d'être remise dans la pool.
        broken = broken or bool(conn.closed)
        if not broken:
            _last_used[id(conn)] = time.monotonic()
        pool.putconn(conn, close=broken)


# ─── Users ────────────────────────────────────────────────────────────────────

def get_all_users(settings: Settings) -> list[dict]:
    with _conn(settings) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT user_id, username, email, password_hash, reset_code, email_verified FROM users")
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


def create_user(
    user_id: str, username: str, email: str, password_hash: str,
    verify_token: str, verify_expires: int, settings: Settings,
) -> None:
    """Crée un compte non activé — l'activation passe par verify_email()."""
    with _conn(settings) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (user_id, username, email, password_hash, email_verified, verify_token, verify_expires) "
                "VALUES (%s, %s, %s, %s, FALSE, %s, %s)",
                (user_id, username, email, password_hash, verify_token, verify_expires),
            )


def delete_user(user_id: str, settings: Settings) -> None:
    with _conn(settings) as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE user_id = %s", (user_id,))


def delete_expired_unverified(username: str, email: str, now: int, settings: Settings) -> None:
    """
    Supprime les comptes jamais activés dont le lien a expiré et qui bloquent ce
    username ou cet email — évite qu'une inscription abandonnée (ou faite avec
    l'email de quelqu'un d'autre) squatte le nom/l'adresse indéfiniment.
    """
    with _conn(settings) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM users WHERE email_verified = FALSE AND verify_expires < %s "
                "AND (LOWER(username) = %s OR LOWER(email) = %s)",
                (now, username.lower(), email.lower()),
            )


def get_user_by_verify_token(token: str, settings: Settings) -> dict | None:
    with _conn(settings) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE verify_token = %s AND verify_token <> ''", (token,))
            row = cur.fetchone()
            return dict(row) if row else None


def set_verify_token(user_id: str, token: str, expires: int, settings: Settings) -> None:
    with _conn(settings) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET verify_token = %s, verify_expires = %s WHERE user_id = %s",
                (token, expires, user_id),
            )


def mark_email_verified(user_id: str, settings: Settings) -> None:
    with _conn(settings) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET email_verified = TRUE, verify_token = '', verify_expires = 0 WHERE user_id = %s",
                (user_id,),
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
