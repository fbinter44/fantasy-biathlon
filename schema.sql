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
    user_id            TEXT PRIMARY KEY,
    top5_h             TEXT DEFAULT '',
    top5_f             TEXT DEFAULT '',
    globe_sprint_h     TEXT DEFAULT '',
    globe_sprint_f     TEXT DEFAULT '',
    globe_pursuit_h    TEXT DEFAULT '',
    globe_pursuit_f    TEXT DEFAULT '',
    globe_individual_h TEXT DEFAULT '',
    globe_individual_f TEXT DEFAULT '',
    globe_mass_start_h TEXT DEFAULT '',
    globe_mass_start_f TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS leagues (
    league_id   TEXT PRIMARY KEY,
    league_name TEXT NOT NULL,
    owner       TEXT NOT NULL,
    members     TEXT DEFAULT '',
    invite_code TEXT UNIQUE NOT NULL
);
