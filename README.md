# Fantasy Biathlon

A full-stack fantasy sports app for the IBU Biathlon World Cup season 2025/26. Users predict season standings before a deadline, earn points based on accuracy, and compete in private leagues.

**Live app:** [fantasy-biathlon.vercel.app](https://fantasy-biathlon.vercel.app)

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, React 18, TypeScript, Tailwind CSS, Recharts |
| Backend | FastAPI, Python 3.12, psycopg2, JWT auth |
| Database | PostgreSQL (Supabase) |
| Deployment | Vercel (frontend) · Railway (backend) |
| Tests | Vitest (frontend) · pytest (backend unit + integration) |

---

## Features

- **Predictions** — submit a top-5 men/women and a globe winner per discipline (sprint, pursuit, individual, mass start) before the season deadline
- **Live scoring** — points computed from real IBU standings; bonus for exact rank prediction (+50 pts) and correct globe winner (+50 pts per discipline)
- **Leaderboard & evolution chart** — fantasy rankings with a race-by-race progression view powered by the IBU API
- **Private leagues** — create a league, share an invite code, compete with friends
- **Auth** — JWT-based login/register, password reset via email (Brevo)

---

## Architecture

```
.
├── backend/              # FastAPI app
│   ├── routers/          # auth, pronostics, classement, leagues, standings, athletes
│   ├── services/         # db.py (psycopg2 pool), email.py
│   ├── models/           # Pydantic request/response schemas
│   └── config.py         # pydantic-settings — reads from .env
│
├── core/                 # Business logic (framework-agnostic)
│   ├── ibu/              # IBU API client — standings, results, evolutive scores
│   ├── scoring/          # Points computation engine
│   └── pronostics/       # Prediction loading & building
│
├── app/                  # Next.js App Router pages
├── components/           # Shared React components
├── lib/                  # API client (lib/api.ts), shared utils
│
└── scripts/              # Data migration, athlete scraping utilities
```

The `core/` layer is intentionally decoupled from both the FastAPI layer and the old Streamlit layer — it can be tested and used independently.

---

## IBU API integration

`core/ibu/IBUClient` wraps the public IBU results service (`biathlonresults.com`). It handles:

- Current World Cup standings per discipline and gender
- Per-race results fetched venue by venue
- Reconstructed race-by-race cumulative standings for the evolution chart
- Smart caching (pickle files) — cache is invalidated only when a new race has completed (5-hour grace period)

---

## Scoring engine

```
Athlete in predicted top-5 and in actual top-10  →  points from rank table (POINTS_TABLE[real_rank])
Predicted rank == real rank                       →  +50 bonus
Correct globe winner (per discipline/gender)      →  +50 bonus
```

Scoring is computed in `core/scoring/` and exposed via `GET /classement`.

---

## Project history

The app was originally built with **Streamlit + Google Sheets** as a rapid prototype. It was later migrated to **FastAPI + Next.js + PostgreSQL** to support a proper separation of concerns, a richer frontend, and production-grade deployment. The `pages/` and `utils/` directories are the original Streamlit app, kept for reference. The migration script (`scripts/migrate_sheets_to_pg.py`) moved user data from Sheets to Supabase.

---

## Local development

### Backend

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements_api.txt

# Create .env with DATABASE_URL, JWT_SECRET, etc.
python -m uvicorn backend.main:app --reload
# → http://localhost:8000/docs
```

### Frontend

```bash
npm install
npm run dev
# → http://localhost:3000
```

### Tests

```bash
# Python
pytest tests/unit/
pytest tests/integration/   # requires a live DB in .env

# Frontend
npm test
```

---

## Environment variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (Supabase session pooler recommended) |
| `JWT_SECRET` | Secret key for token signing |
| `BREVO_API_KEY` | Transactional email for password reset |
| `BREVO_SENDER` | Sender address |
