import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Configuration globale de l'application.
    Les variables sont lues depuis l'environnement.
    En local, un fichier .env peut être utilisé (optionnel).
    """

    LLM_PROVIDER: str = Field(default="openai")
    OPENAI_API_KEY: str | None = Field(default=None)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
