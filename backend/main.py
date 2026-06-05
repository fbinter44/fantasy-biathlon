"""
Point d'entrée FastAPI — MPG Biathlon API.

Lancer en dev :
    uvicorn api.main:app --reload

Swagger UI : http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import auth, standings, pronostics, classement, leagues, athletes

app = FastAPI(
    title="MPG Biathlon API",
    description="Backend FastAPI pour l'app Fantasy Biathlon 2025/26.",
    version="1.0.0",
)

# ---------------------------------------------------------
# CORS — à restreindre en production avec l'URL Next.js réelle
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://clean-shot.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Routers
# ---------------------------------------------------------
app.include_router(auth.router)
app.include_router(athletes.router)
app.include_router(standings.router)
app.include_router(pronostics.router)
app.include_router(classement.router)
app.include_router(leagues.router)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "version": "1.0.0"}
