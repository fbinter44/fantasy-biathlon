-- Schema PostgreSQL — Fantasy Biathlon
-- À exécuter dans Supabase : SQL Editor → New query → Run

CREATE TABLE IF NOT EXISTS users (
    user_id       TEXT PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    reset_code    TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS pronostics (
    user_id            TEXT NOT NULL,
    season             TEXT NOT NULL DEFAULT '2526',
    top5_h             TEXT DEFAULT '',
    top5_f             TEXT DEFAULT '',
    globe_sprint_h     TEXT DEFAULT '',
    globe_sprint_f     TEXT DEFAULT '',
    globe_pursuit_h    TEXT DEFAULT '',
    globe_pursuit_f    TEXT DEFAULT '',
    globe_individual_h TEXT DEFAULT '',
    globe_individual_f TEXT DEFAULT '',
    globe_mass_start_h TEXT DEFAULT '',
    globe_mass_start_f TEXT DEFAULT '',
    PRIMARY KEY (user_id, season)
);

CREATE TABLE IF NOT EXISTS leagues (
    league_id   TEXT PRIMARY KEY,
    league_name TEXT NOT NULL,
    owner       TEXT NOT NULL,
    members     TEXT DEFAULT '',
    invite_code TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS race_pronostics (
    user_id TEXT NOT NULL,
    race_id TEXT NOT NULL,
    ibu_id  TEXT NOT NULL,
    season  TEXT NOT NULL DEFAULT '2526',
    PRIMARY KEY (user_id, race_id, season)
);

-- ─── Migration saison (à exécuter sur une base existante) ────────────────────
-- ALTER TABLE pronostics ADD COLUMN IF NOT EXISTS season TEXT NOT NULL DEFAULT '2526';
-- ALTER TABLE pronostics DROP CONSTRAINT IF EXISTS pronostics_pkey;
-- ALTER TABLE pronostics ADD PRIMARY KEY (user_id, season);
--
-- ALTER TABLE race_pronostics ADD COLUMN IF NOT EXISTS season TEXT NOT NULL DEFAULT '2526';
-- ALTER TABLE race_pronostics DROP CONSTRAINT IF EXISTS race_pronostics_pkey;
-- ALTER TABLE race_pronostics ADD PRIMARY KEY (user_id, race_id, season);
