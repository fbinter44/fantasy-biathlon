# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

```bash
streamlit run App.py
```

The app uses Python 3.12. There are no automated tests and no lint configuration. The `dev_runner.py` script at the root can be used for local development utilities.

## Architecture overview

This is a French-language **Fantasy Biathlon** Streamlit app for the 2025/26 season. Users predict biathlon season winners before the deadline (`PRONOS_DEADLINE` in `utils/biathlon_data.py`), earn points based on accuracy, and compete in leagues.

### Page routing

`App.py` is the landing page. All numbered pages in `pages/` are auto-routed by Streamlit:
- `0_Login.py` — auth (login / register / reset)
- `1_Pronostics_Modifier.py` — submit/edit predictions
- `2_Pronostics_Tous.py` / `2b_Pronostics_Biathlete.py` — view all predictions
- `3_Classement.py` / `3b_Evolution_Classement.py` — fantasy leaderboard and its evolution over the season
- `4_Resultats_Officiels.py` — official IBU standings with prediction highlights
- `5_Reglement.py` — rules
- `6_Mon_Compte.py` / `7_Mes_Ligues.py` — account and league management

### Data sources

**IBU API** (`core/ibu/`) — wraps `https://bw.biathlonresults.com`. `IBUClient` is the single entry point:
- `load_standings()` → current World Cup standings (top 10 per discipline, per gender)
- `load_results()` → per-race results via venues/competitions
- `compute_cumulated_scores()` / `compute_evolutive_standings()` → standings reconstructed race by race (for the evolution chart)
- `get_season_progress()` → how many races completed vs. total per discipline

**Google Sheets** (`utils/sheets.py`) — stores all user data. Three worksheets matter:
- `Users` — user_id, username, email, password_hash, reset_code
- `Pronostics` — one row per user: top5_h, top5_f, and per-discipline globe winners
- `Leagues` — league_id, league_name, owner, members (comma-separated user_ids), invite_code

Access goes through `read_all(name)` / `get_sheet(name)`. Credentials come from `st.secrets["gcp_service_account"]` and `st.secrets["sheets"]["sheet_id"]`.

**Static athlete data** — `biathletes_data/athletes_info.json` is the master list, loaded at import time into `ATHLETES_BY_IBUID` in `utils/biathlon_data.py`. IBUId is the canonical athlete identifier throughout the app.

### Scoring (`core/scoring/`)

- A prediction stores a top-5 men and top-5 women (for the general standings), plus one winner per discipline per gender (the "globes").
- Points from `compute_regular_points`: each predicted athlete in the actual top 10 earns points from `POINTS_TABLE` (indexed by real rank 1–10). +50 bonus if predicted rank matches real rank.
- Globe winner correct prediction: +50 per discipline per gender.
- `PlayerPoints` accumulates all these into a total for the fantasy leaderboard.

### Caching

IBU standings are pickled under `cache/cache_standings/` and refreshed only when the cache pre-dates the last completed race (with a 5-hour grace period). Race/venue results use `cache/cache_venues` and `cache/cache_results`. Google Sheets reads for Pronostics and Leagues are JSON-cached in `cache/cache_pronos` and `cache/cache_leagues`.

### Auth & session state

Passwords are hashed with bcrypt. Password reset codes are stored in the `reset_code` column of the `Users` sheet and emailed via Brevo (`st.secrets["brevo"]`). Session state keys: `"user"` (user_id), `"current_league"` (league_id), `"current_page"`.

### Key constants (`utils/biathlon_data.py`)

- `DISCIPLINES_DISPLAY` — ordered list of `(attr, display_name)` pairs that drives all discipline tabs
- `DISCIPLINES_WINNERS` — maps discipline attr → prediction field name
- `BIATHLETES_H` / `BIATHLETES_F` — IBUIds split by gender, derived from the JSON at import time
- Season code `"2526"` = season 2025/26; used in IBU API URL construction
