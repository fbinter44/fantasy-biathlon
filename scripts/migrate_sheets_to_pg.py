"""
Script de migration : Google Sheets → PostgreSQL

Usage :
    python scripts/migrate_sheets_to_pg.py

Nécessite les deux dans .env :
    - gcp_service_account_json + sheet_id  (source)
    - database_url                          (destination)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api.config import get_settings
from api.services import sheets as src
from api.services import db as dst


def migrate():
    settings = get_settings()

    if not settings.database_url:
        print("❌ DATABASE_URL manquant dans .env")
        sys.exit(1)
    if not settings.gcp_service_account_json:
        print("❌ GCP_SERVICE_ACCOUNT_JSON manquant dans .env")
        sys.exit(1)

    print("📖 Lecture depuis Google Sheets...")
    users      = src.read_all("Users",      settings)
    pronos     = src.read_all("Pronostics", settings)
    leagues    = src.read_all("Leagues",    settings)

    print(f"   {len(users)} users | {len(pronos)} pronostics | {len(leagues)} ligues")

    # ── Users ──────────────────────────────────────────────────────────────────
    print("\n👤 Migration des users...")
    ok = err = 0
    for u in users:
        try:
            dst.create_user(
                user_id=u["user_id"],
                username=u["username"],
                email=u["email"],
                password_hash=u["password_hash"],
                settings=settings,
            )
            if u.get("reset_code"):
                dst.update_user_field(u["user_id"], "reset_code", u["reset_code"], settings)
            ok += 1
        except Exception as e:
            print(f"   ⚠️  {u.get('username')} : {e}")
            err += 1
    print(f"   ✅ {ok} insérés, ⚠️  {err} erreurs (doublons éventuels ignorés)")

    # ── Pronostics ─────────────────────────────────────────────────────────────
    print("\n🎯 Migration des pronostics...")
    ok = err = 0
    for p in pronos:
        try:
            dst.upsert_pronostics(
                user_id=p["user_id"],
                settings=settings,
                top5_h=p.get("top5_h", ""),
                top5_f=p.get("top5_f", ""),
                globe_sprint_h=p.get("globe_sprint_h", ""),
                globe_sprint_f=p.get("globe_sprint_f", ""),
                globe_pursuit_h=p.get("globe_pursuit_h", ""),
                globe_pursuit_f=p.get("globe_pursuit_f", ""),
                globe_individual_h=p.get("globe_individual_h", ""),
                globe_individual_f=p.get("globe_individual_f", ""),
                globe_mass_start_h=p.get("globe_mass_start_h", ""),
                globe_mass_start_f=p.get("globe_mass_start_f", ""),
            )
            ok += 1
        except Exception as e:
            print(f"   ⚠️  {p.get('user_id')} : {e}")
            err += 1
    print(f"   ✅ {ok} insérés, ⚠️  {err} erreurs")

    # ── Leagues ────────────────────────────────────────────────────────────────
    print("\n🏔️  Migration des ligues...")
    ok = err = 0
    for lg in leagues:
        try:
            dst.create_league(
                league_id=lg["league_id"],
                name=lg["league_name"],
                owner=lg["owner"],
                members=lg.get("members", ""),
                invite_code=lg.get("invite_code", ""),
                settings=settings,
            )
            ok += 1
        except Exception as e:
            print(f"   ⚠️  {lg.get('league_name')} : {e}")
            err += 1
    print(f"   ✅ {ok} insérées, ⚠️  {err} erreurs")

    print("\n🎉 Migration terminée !")


if __name__ == "__main__":
    migrate()
