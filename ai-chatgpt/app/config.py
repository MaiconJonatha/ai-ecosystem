"""
Configuracoes do AI ChatGPT
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI ChatGPT"
    database_url: str = "sqlite+aiosqlite:///./ai_chat.db"
    secret_key: str = "ai-chatgpt-secret-key-2024"
    ollama_url: str = "http://localhost:11434"

    class Config:
        env_file = ".env"


settings = Settings()
