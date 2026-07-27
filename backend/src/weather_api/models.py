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
MapLayerKind = Literal["tile", "fires", "air-quality", "observation-points"]


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


class MapLegendEntry(BaseModel):
    label: str
    color: str


class MapLayerLegend(BaseModel):
    title: str
    units: str | None = None
    entries: list[MapLegendEntry] = Field(default_factory=list)
    note: str | None = None


class MapLayer(BaseModel):
    id: str
    label: str
    kind: MapLayerKind
    description: str
    enabled: bool = True
    unavailable_reason: str | None = None
    tile_url: str | None = None
    data_url: str | None = None
    source: str
    attribution: str
    updated_at: datetime | None = None
    legend: MapLayerLegend


class MapPanel(BaseModel):
    default_layer_id: str
    cycle_seconds: int = 8
    zoom: int = 6
    overlay_opacity: float = 0.65
    layers: list[MapLayer] = Field(default_factory=list)


class FirePoint(BaseModel):
    latitude: float
    longitude: float
    distance_km: float
    confidence: str | None = None
    brightness: float | None = None
    acquired_at: datetime | None = None
    satellite: str | None = None


class FiresOverlayPayload(BaseModel):
    source: str
    fetched_at: datetime
    updated_at: datetime | None = None
    points: list[FirePoint] = Field(default_factory=list)


class AirQualityObservation(BaseModel):
    latitude: float
    longitude: float
    aqi: int
    category: str
    pollutant: str
    reporting_area: str
    state_code: str | None = None
    distance_miles: float
    observed_at: datetime | None = None


class AirQualityOverlayPayload(BaseModel):
    source: str
    fetched_at: datetime
    updated_at: datetime | None = None
    observations: list[AirQualityObservation] = Field(default_factory=list)


ObservationMetric = Literal["temperature", "wind"]


class WeatherObservationPoint(BaseModel):
    latitude: float
    longitude: float
    value: float
    unit: str
    station_id: str
    station_name: str | None = None
    wind_direction: str | None = None
    observed_at: datetime | None = None


class WeatherObservationOverlayPayload(BaseModel):
    metric: ObservationMetric
    source: str
    fetched_at: datetime
    updated_at: datetime | None = None
    points: list[WeatherObservationPoint] = Field(default_factory=list)


class WeatherPayload(BaseModel):
    location: Location
    current: CurrentConditions
    hourly: list[ForecastPeriod]
    daily: list[ForecastPeriod]
    alerts: list[Alert]
    recommendations: Recommendations
    metadata: WeatherMetadata
    map_panel: MapPanel
