import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator

class Settings(BaseSettings):
    """
    Centralized application settings using pydantic-settings.
    Environment variables are automatically loaded from .env if present.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Required Settings
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")

    # Optional Settings with Defaults
    location_city: str = Field("Dublin", alias="LOCATION_CITY")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    ingredient_confidence_threshold: float = Field(0.0, alias="INGREDIENT_CONFIDENCE_THRESHOLD")

    @validator("log_level")
    def validate_log_level(cls, v):
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed:
            return "INFO"
        return v.upper()

    @validator("ingredient_confidence_threshold")
    def validate_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("INGREDIENT_CONFIDENCE_THRESHOLD must be between 0.0 and 1.0")
        return v

# Global settings instance
settings = Settings()
