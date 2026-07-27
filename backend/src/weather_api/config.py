from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT_ENV, ".env"),
        env_file_encoding="utf-8",
    )

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
    map_timeout_seconds: float = Field(default=10.0, alias="MAP_TIMEOUT_SECONDS")
    map_cycle_seconds: int = Field(default=8, alias="MAP_CYCLE_SECONDS")
    map_default_zoom: int = Field(default=6, alias="MAP_DEFAULT_ZOOM")
    map_overlay_opacity: float = Field(default=0.65, alias="MAP_OVERLAY_OPACITY")
    map_cache_ttl_seconds: int = Field(default=600, alias="MAP_CACHE_TTL_SECONDS")
    map_observation_station_limit: int = Field(default=25, alias="MAP_OBSERVATION_STATION_LIMIT")
    map_observation_point_limit: int = Field(default=40, alias="MAP_OBSERVATION_POINT_LIMIT")

    # Deprecated, retained to avoid startup failures when existing .env files still include it.
    openweather_api_key: str | None = Field(default=None, alias="OPENWEATHER_API_KEY")
    airnow_api_key: str | None = Field(default=None, alias="AIRNOW_API_KEY")
    airnow_base_url: str = Field(default="https://www.airnowapi.org", alias="AIRNOW_BASE_URL")
    airnow_search_distance_miles: int = Field(default=75, alias="AIRNOW_SEARCH_DISTANCE_MILES")
    airnow_max_observations: int = Field(default=150, alias="AIRNOW_MAX_OBSERVATIONS")
    rainviewer_api_url: str = Field(
        default="https://api.rainviewer.com/public/weather-maps.json",
        alias="RAINVIEWER_API_URL",
    )

    firms_viirs_snpp_csv_url: str = Field(
        default="https://firms.modaps.eosdis.nasa.gov/data/active_fire/viirs-snpp-nrt/csv/SUOMI_VIIRS_C2_Global_24h.csv",
        alias="FIRMS_VIIRS_SNPP_CSV_URL",
    )
    firms_viirs_noaa20_csv_url: str = Field(
        default="https://firms.modaps.eosdis.nasa.gov/data/active_fire/viirs-noaa20-nrt/csv/J1_VIIRS_C2_Global_24h.csv",
        alias="FIRMS_VIIRS_NOAA20_CSV_URL",
    )
    firms_search_radius_km: float = Field(default=400.0, alias="FIRMS_SEARCH_RADIUS_KM")
    firms_max_points: int = Field(default=200, alias="FIRMS_MAX_POINTS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
