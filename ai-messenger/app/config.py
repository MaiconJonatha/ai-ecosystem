"""Configurações do AI Messenger"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "AI Messenger"
    database_url: str = "sqlite+aiosqlite:///./ai_messenger.db"
    secret_key: str = "ai-messenger-secret-2024"
    ollama_url: str = "http://localhost:11434"

    class Config:
        env_file = ".env"

settings = Settings()
