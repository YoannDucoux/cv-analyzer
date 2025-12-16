import os
from pathlib import Path

# Charger depuis .env si disponible
def load_env_file():
    """Charge les variables d'environnement depuis un fichier .env"""
    # Chercher .env dans le dossier backend (parent de app/)
    env_path = Path(__file__).parent.parent.parent / ".env"
    # Alternative: chercher aussi à la racine du projet
    if not env_path.exists():
        env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value

# Charger le .env avant de créer les settings
load_env_file()

class Settings:
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "none")
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")

settings = Settings()
