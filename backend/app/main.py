from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import router

app = FastAPI(title="CV Analyzer", version="0.1.0")

# MVP: CORS ouvert pour permettre au front local d'appeler l'API.
# En production, on restreindra allow_origins à ton domaine.
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://6942d3e2bde5e3860c376944--cv-analyzer-api.netlify.app",
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok"}
