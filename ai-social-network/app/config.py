from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "AI Social Network"
    debug: bool = True

    # Database
    database_url: str = "sqlite+aiosqlite:///./ai_social.db"

    # JWT
    secret_key: str = "sua-chave-secreta-super-segura-aqui-mude-em-producao"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 dias

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
