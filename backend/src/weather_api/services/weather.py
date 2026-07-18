from datetime import datetime, timezone
from typing import Any

import httpx

from weather_api.clients import NwsClient
from weather_api.config import Settings
from weather_api.models import (
    Alert,
    CurrentConditions,
    ForecastPeriod,
    Location,
    Recommendations,
    WeatherMetadata,
    WeatherPayload,
)
from weather_api.services.cache import WeatherCache
from weather_api.services.golf import calculate_golf_recommendation
from weather_api.services.lawn import calculate_lawn_recommendation
from weather_api.telemetry import set_weather_metrics


class WeatherService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._http_client = httpx.AsyncClient()
        self._nws = NwsClient(self._http_client, settings)
        self._cache = WeatherCache(
            ttl_seconds=settings.cache_ttl_seconds,
            stale_max_seconds=settings.stale_data_max_seconds,
        )

    async def shutdown(self) -> None:
        await self._http_client.aclose()

    async def get_dashboard_weather(self) -> WeatherPayload:
        payload = await self._cache.get_weather(self._fetch_fresh_weather)
        set_weather_metrics(payload)
        return payload

    def ready_status(self) -> tuple[bool, str]:
        status = self._cache.get_status()
        if not status.has_data:
            return False, "No successful weather refresh has completed yet"
        if status.age_seconds > self._settings.stale_data_max_seconds:
            return False, "Cached data is older than allowed stale threshold"
        if status.stale:
            return True, "Serving stale data within allowed threshold"
        return True, "Serving fresh weather data"

    async def _fetch_fresh_weather(self) -> WeatherPayload:
        raw = await self._nws.fetch_raw_weather(
            latitude=self._settings.weather_latitude,
            longitude=self._settings.weather_longitude,
        )

        current = _normalize_current(raw.get("observation", {}))
        hourly = _normalize_periods(raw.get("hourly", {}), limit=48)
        daily = _normalize_periods(raw.get("forecast", {}), limit=14)
        alerts = _normalize_alerts(raw.get("alerts", {}))

        recommendations = Recommendations(
            golf=calculate_golf_recommendation(hourly=hourly, alerts=alerts),
            lawn=calculate_lawn_recommendation(hourly=hourly, current=current, alerts=alerts),
        )

        generated_at = datetime.now(timezone.utc)
        metadata = WeatherMetadata(
            source="National Weather Service",
            generated_at=generated_at,
            last_successful_refresh=generated_at,
            stale=False,
            cache_age_seconds=0,
        )

        return WeatherPayload(
            location=Location(
                name=self._settings.weather_location_name,
                latitude=self._settings.weather_latitude,
                longitude=self._settings.weather_longitude,
                timezone=self._settings.weather_timezone,
            ),
            current=current,
            hourly=hourly,
            daily=daily,
            alerts=alerts,
            recommendations=recommendations,
            metadata=metadata,
        )


def _normalize_current(observation_payload: dict[str, Any]) -> CurrentConditions:
    props = _safe_dict(observation_payload.get("properties"))
    temperature_c = _nested_numeric(props, "temperature", "value")
    dewpoint_c = _nested_numeric(props, "dewpoint", "value")
    humidity = _nested_numeric(props, "relativeHumidity", "value")
    wind_speed_raw = _nested_numeric(props, "windSpeed", "value")
    wind_gust_raw = _nested_numeric(props, "windGust", "value")

    return CurrentConditions(
        observed_at=_parse_datetime(props.get("timestamp")),
        temperature_f=_c_to_f(temperature_c),
        feels_like_f=_c_to_f(temperature_c if dewpoint_c is None else (temperature_c + dewpoint_c) / 2),
        relative_humidity_percent=humidity,
        wind_speed_mph=_mps_to_mph(wind_speed_raw),
        wind_gust_mph=_mps_to_mph(wind_gust_raw),
        wind_direction=_wind_direction(props),
        conditions=_safe_str(props.get("textDescription")),
        icon_url=_safe_str(props.get("icon")),
    )


def _normalize_periods(payload: dict[str, Any], *, limit: int) -> list[ForecastPeriod]:
    periods = _safe_list(_safe_dict(payload.get("properties")).get("periods"))
    normalized: list[ForecastPeriod] = []
    for period in periods[:limit]:
        if not isinstance(period, dict):
            continue
        temp_value = _to_float(period.get("temperature"))
        temperature_unit = _safe_str(period.get("temperatureUnit")) or "F"
        wind_speed, wind_gust = _parse_wind_values(_safe_str(period.get("windSpeed")))
        precip = _nested_numeric(period, "probabilityOfPrecipitation", "value")

        start = _parse_datetime(period.get("startTime"))
        end = _parse_datetime(period.get("endTime"))
        if start is None or end is None:
            continue

        if temperature_unit.upper() == "C":
            temperature_f = _c_to_f(temp_value)
        else:
            temperature_f = temp_value

        normalized.append(
            ForecastPeriod(
                start=start,
                end=end,
                name=_safe_str(period.get("name")),
                is_daytime=bool(period.get("isDaytime", True)),
                temperature_f=temperature_f,
                wind_speed_mph=wind_speed,
                wind_gust_mph=wind_gust,
                precip_probability_percent=precip,
                conditions=_safe_str(period.get("shortForecast") or period.get("detailedForecast")),
                icon_url=_safe_str(period.get("icon")),
            )
        )
    return normalized


def _normalize_alerts(payload: dict[str, Any]) -> list[Alert]:
    features = _safe_list(payload.get("features"))
    alerts: list[Alert] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        props = _safe_dict(feature.get("properties"))
        alert_id = _safe_str(feature.get("id")) or _safe_str(props.get("id"))
        if alert_id is None:
            continue
        alerts.append(
            Alert(
                id=alert_id,
                event=_safe_str(props.get("event")),
                severity=_safe_str(props.get("severity")),
                headline=_safe_str(props.get("headline")),
                description=_safe_str(props.get("description")),
                effective=_parse_datetime(props.get("effective")),
                expires=_parse_datetime(props.get("expires")),
                status=_safe_str(props.get("status")),
            )
        )
    return alerts


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_str(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    return None


def _to_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _nested_numeric(payload: dict[str, Any], outer_key: str, inner_key: str) -> float | None:
    outer = _safe_dict(payload.get(outer_key))
    return _to_float(outer.get(inner_key))


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _c_to_f(celsius: float | None) -> float | None:
    if celsius is None:
        return None
    return round((celsius * 9 / 5) + 32, 1)


def _mps_to_mph(mps: float | None) -> float | None:
    if mps is None:
        return None
    return round(mps * 2.23694, 1)


def _wind_direction(props: dict[str, Any]) -> str | None:
    direction_value = _nested_numeric(props, "windDirection", "value")
    if direction_value is None:
        return _safe_str(props.get("windDirection"))

    labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = int(((direction_value + 22.5) % 360) / 45)
    return labels[index]


def _parse_wind_values(wind_speed_field: str | None) -> tuple[float | None, float | None]:
    if wind_speed_field is None:
        return None, None

    numbers: list[float] = []
    current = ""
    for char in wind_speed_field:
        if char.isdigit() or char == ".":
            current += char
            continue
        if current:
            numbers.append(float(current))
            current = ""
    if current:
        numbers.append(float(current))

    if len(numbers) == 0:
        return None, None
    if len(numbers) == 1:
        return round(numbers[0], 1), None
    return round(sum(numbers[:2]) / 2, 1), round(max(numbers[:2]), 1)
