"""
Конфигурация приложения
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # Telegram Bot
    BOT_TOKEN: str
    WEBAPP_URL: str
    
    # Database
    DATABASE_PATH: str = "database/game.db"
    
    # Server
    WEBAPP_HOST: str = "0.0.0.0"
    WEBAPP_PORT: int = 8080
    
    # Game Settings
    INITIAL_INCOME_PER_HOUR: int = 10
    INITIAL_GUESTS_PER_HOUR: int = 2
    OFFLINE_INCOME_MAX_HOURS: int = 24
    
    # Development
    DEBUG: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Глобальный экземпляр настроек
settings = Settings()
