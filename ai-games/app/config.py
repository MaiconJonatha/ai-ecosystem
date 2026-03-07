from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "AI Games"
    ollama_url: str = "http://localhost:11434"

settings = Settings()
