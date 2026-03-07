"""
Configuracoes do AI Search Engine
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Search Engine"
    database_url: str = "sqlite+aiosqlite:///./ai_search.db"
    secret_key: str = "ai-search-engine-secret-key-2024"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 1 semana
    ollama_url: str = "http://localhost:11434"

    class Config:
        env_file = ".env"


settings = Settings()
