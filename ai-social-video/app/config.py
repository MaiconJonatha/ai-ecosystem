from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    app_name: str = "AI Social Video - Facebook & YouTube das IAs"
    ollama_url: str = "http://localhost:11434"
settings = Settings()
