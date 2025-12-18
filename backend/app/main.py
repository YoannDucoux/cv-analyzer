from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import router
from .core.config import settings

app = FastAPI(title="CV Analyzer", version="0.1.0")

# Configuration CORS depuis variable d'environnement
cors_origins = [
    origin.strip()
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/api/v1/health")
def health():
    """Endpoint de santé pour vérifier que le backend est accessible."""
    return {"status": "ok"}
