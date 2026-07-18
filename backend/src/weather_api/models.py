from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Location(BaseModel):
    name: str
    latitude: float
    longitude: float
    timezone: str


class CurrentConditions(BaseModel):
    observed_at: datetime | None = None
    temperature_f: float | None = None
    feels_like_f: float | None = None
    relative_humidity_percent: float | None = None
    wind_speed_mph: float | None = None
    wind_gust_mph: float | None = None
    wind_direction: str | None = None
    conditions: str | None = None
    icon_url: str | None = None


class ForecastPeriod(BaseModel):
    start: datetime
    end: datetime
    name: str | None = None
    is_daytime: bool = True
    temperature_f: float | None = None
    wind_speed_mph: float | None = None
    wind_gust_mph: float | None = None
    precip_probability_percent: float | None = None
    conditions: str | None = None
    icon_url: str | None = None


class Alert(BaseModel):
    id: str
    event: str | None = None
    severity: str | None = None
    headline: str | None = None
    description: str | None = None
    effective: datetime | None = None
    expires: datetime | None = None
    status: str | None = None


GolfLabel = Literal["Excellent", "Good", "Playable", "Poor", "Avoid"]
LawnRecommendationType = Literal["Water", "Skip", "Delay", "Optional"]
ConfidenceLevel = Literal["low", "medium", "high"]


class GolfBestWindow(BaseModel):
    start: datetime | None = None
    end: datetime | None = None


class GolfRecommendation(BaseModel):
    score: int
    label: GolfLabel
    best_window: GolfBestWindow
    summary: str
    reasons: list[str] = Field(default_factory=list)
    limited_data: bool = False


class LawnRecommendation(BaseModel):
    recommendation: LawnRecommendationType
    confidence: ConfidenceLevel
    suggested_time: str
    summary: str
    reasons: list[str] = Field(default_factory=list)
    disclaimer: str


class Recommendations(BaseModel):
    golf: GolfRecommendation
    lawn: LawnRecommendation


class WeatherMetadata(BaseModel):
    source: str = "National Weather Service"
    generated_at: datetime
    last_successful_refresh: datetime | None = None
    stale: bool = False
    cache_age_seconds: int = 0
    status_message: str | None = None


class WeatherPayload(BaseModel):
    location: Location
    current: CurrentConditions
    hourly: list[ForecastPeriod]
    daily: list[ForecastPeriod]
    alerts: list[Alert]
    recommendations: Recommendations
    metadata: WeatherMetadata
