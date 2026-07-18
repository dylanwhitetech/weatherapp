from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    weather_location_name: str = Field(default="Walla Walla, WA", alias="WEATHER_LOCATION_NAME")
    weather_latitude: float = Field(default=46.0646, alias="WEATHER_LATITUDE")
    weather_longitude: float = Field(default=-118.3430, alias="WEATHER_LONGITUDE")
    weather_timezone: str = Field(default="America/Los_Angeles", alias="WEATHER_TIMEZONE")
    nws_user_agent: str = Field(
        default="weatherapp/0.1 (replace-with-contact@example.com)",
        alias="NWS_USER_AGENT",
    )

    cache_ttl_seconds: int = Field(default=600, alias="CACHE_TTL_SECONDS")
    stale_data_max_seconds: int = Field(default=3600, alias="STALE_DATA_MAX_SECONDS")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    nws_base_url: str = Field(default="https://api.weather.gov", alias="NWS_BASE_URL")
    nws_timeout_seconds: float = Field(default=10.0, alias="NWS_TIMEOUT_SECONDS")
    nws_max_retries: int = Field(default=2, alias="NWS_MAX_RETRIES")
    nws_backoff_seconds: float = Field(default=0.3, alias="NWS_BACKOFF_SECONDS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
