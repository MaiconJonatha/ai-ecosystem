from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "AI Crypto Exchange"
    ollama_url: str = "http://localhost:11434"

settings = Settings()
