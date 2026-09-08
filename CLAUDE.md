# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

### Backend (FastAPI)
```bash
python -m uvicorn backend.main:app --reload
# → http://localhost:8000/docs
```

### Frontend (Next.js)
```bash
npm run dev
# → http://localhost:3000
```

The project uses Python 3.12 and Node.js 20.

## Architecture overview

This is a French-language **Fantasy Biathlon** app. Users predict biathlon season winners before the deadline, earn points based on accuracy, and compete in leagues.

Stack: **FastAPI + Next.js + PostgreSQL (Supabase)**.

### Deployment

- **Frontend**: Vercel (`vercel.json` at root forces Next.js detection)
- **Backend**: Railway (`railway.json` at root, `requirements.txt`)
- **Database**: Supabase PostgreSQL — use the **Session pooler** connection string in `DATABASE_URL` (Railway is IPv4-only)

### Directory structure

```
backend/          FastAPI app (routers, services, models, config)
core/             Business logic — framework-agnostic
  ibu/            IBU API client
  scoring/        Points computation engine
  pronostics/     Prediction loading & building
app/              Next.js App Router pages
components/       React components (Header, Logo, AppGuard, SeasonGuard…)
context/          React contexts (AuthContext, SeasonContext)
lib/              API client (lib/api.ts), season utils (lib/season.ts)
utils/            Shared Python constants & helpers (biathlon_data, cache_helpers, api_helpers, sheets)
biathletes_data/  Static athlete master list (athletes_info.json)
scripts/          One-off data utilities
tests/
  unit/           pytest unit tests (scoring, biathlon data)
  integration/    pytest integration tests (require live DB)
  frontend/       Vitest tests
```

### Backend (`backend/`)

**Entry point**: `backend/main.py` — FastAPI app with CORS middleware.

**Routers**: `auth`, `pronostics`, `classement`, `leagues`, `standings`, `athletes`

**Config** (`backend/config.py`): `pydantic-settings` reads from `.env`. Key vars:
- `DATABASE_URL` — PostgreSQL connection string (Supabase session pooler)
- `JWT_SECRET` — token signing key
- `BREVO_API_KEY` / `BREVO_SENDER` — transactional email for password reset
- `IBU_SEASON_CODE` — defaults to `"2526"`

**DB service** (`backend/services/db.py`): `psycopg2.ThreadedConnectionPool` singleton. Appends `?sslmode=require` if not present. All DB functions take `Settings` as a parameter (injected via FastAPI dependency).

**Auth**: JWT (python-jose), bcrypt password hashing. Tokens expire after 7 days.

### Core layer (`core/`)

**IBU API** (`core/ibu/`) — wraps `https://bw.biathlonresults.com`. `IBUClient` is the single entry point:
- `load_standings()` → current World Cup standings (top 10 per discipline, per gender)
- `load_results()` → per-race results via venues/competitions
- `compute_cumulated_scores()` / `compute_evolutive_standings()` → standings reconstructed race by race
- `get_season_progress()` → races completed vs. total per discipline

Caching: standings pickled under `cache/cache_standings/`, refreshed only when cache pre-dates the last completed race (5-hour grace period). Venues/results cached in `cache/cache_venues` and `cache/cache_results`.

**Scoring** (`core/scoring/`):
- `compute_regular_points`: each predicted athlete in actual top 10 earns points from `POINTS_TABLE[real_rank - 1]`. +50 bonus if predicted rank == real rank.
- Globe winner correct: +50 per discipline per gender.
- `PlayerPoints` accumulates total for the fantasy leaderboard.

**Static athlete data** — `biathletes_data/athletes_info.json` is the master list. IBUId is the canonical athlete identifier throughout the app.

### Frontend (`app/`, `components/`, `lib/`)

Next.js 14 App Router. All API calls go through `lib/api.ts` which reads `NEXT_PUBLIC_API_URL`.

Pages: `login`, `pronostics`, `pronostics/modifier`, `pronostics/biathlete`, `classement`, `classement/evolution`, `resultats`, `ligues`, `compte`, `reglement`, `reset-password`.

Charts use Recharts. Country flags use `flag-icons`.

### Key constants (`utils/biathlon_data.py`) — used by both stacks

- `DISCIPLINES_DISPLAY` — ordered list of `(attr, display_name)` pairs
- `DISCIPLINES_WINNERS` — maps discipline attr → prediction field name
- `BIATHLETES_H` / `BIATHLETES_F` — IBUIds split by gender
- Season code `"2526"` = season 2025/26

### Tests

```bash
pytest tests/unit/
pytest tests/integration/   # requires DATABASE_URL in .env
npm test                     # Vitest — tests/frontend/
```
