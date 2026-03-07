"""
Configurações do AI WhatsApp
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI WhatsApp"
    database_url: str = "sqlite+aiosqlite:///./ai_whatsapp.db"
    secret_key: str = "ai-whatsapp-secret-2024"
    ollama_url: str = "http://localhost:11434"

    class Config:
        env_file = ".env"


settings = Settings()
