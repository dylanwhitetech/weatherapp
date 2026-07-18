from datetime import datetime, timezone

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from weather_api.models import WeatherPayload

REQUESTS_TOTAL = Counter(
    "weather_api_requests_total",
    "Count of HTTP requests served by route/method/status",
    ["route", "method", "status"],
)
REQUEST_DURATION_SECONDS = Histogram(
    "weather_api_request_duration_seconds",
    "HTTP request latency by route/method",
    ["route", "method"],
)
UPSTREAM_REQUESTS_TOTAL = Counter(
    "weather_upstream_requests_total",
    "Count of upstream requests by endpoint/result",
    ["endpoint", "result"],
)
UPSTREAM_REQUEST_DURATION_SECONDS = Histogram(
    "weather_upstream_request_duration_seconds",
    "Duration of upstream weather requests by endpoint",
    ["endpoint"],
)
UPSTREAM_ERRORS_TOTAL = Counter(
    "weather_upstream_errors_total",
    "Count of upstream weather errors by endpoint/error_type",
    ["endpoint", "error_type"],
)

CACHE_HITS_TOTAL = Counter("weather_cache_hits_total", "Count of weather cache hits")
CACHE_MISSES_TOTAL = Counter("weather_cache_misses_total", "Count of weather cache misses")
CACHE_AGE_SECONDS = Gauge("weather_cache_age_seconds", "Age of cached weather payload in seconds")
LAST_SUCCESSFUL_REFRESH_TIMESTAMP_SECONDS = Gauge(
    "weather_last_successful_refresh_timestamp_seconds",
    "Unix timestamp of the last successful refresh",
)
WEATHER_DATA_STALE = Gauge(
    "weather_data_stale",
    "1 when serving stale weather data; otherwise 0",
)

WEATHER_TEMPERATURE_F = Gauge("weather_temperature_fahrenheit", "Current temperature in Fahrenheit")
WEATHER_FEELS_LIKE_F = Gauge(
    "weather_feels_like_fahrenheit",
    "Current feels-like temperature in Fahrenheit",
)
WEATHER_HUMIDITY = Gauge("weather_relative_humidity_percent", "Current relative humidity percent")
WEATHER_WIND_SPEED = Gauge("weather_wind_speed_mph", "Current sustained wind speed in mph")
WEATHER_WIND_GUST = Gauge("weather_wind_gust_mph", "Current wind gust in mph")
WEATHER_PRECIP = Gauge(
    "weather_precipitation_probability_percent",
    "Precipitation probability for common windows",
    ["period"],
)
WEATHER_ACTIVE_ALERTS = Gauge("weather_active_alerts", "Count of active alerts by severity", ["severity"])
WEATHER_GOLF_SCORE = Gauge("weather_golf_score", "Current golf recommendation score")
WEATHER_LAWN_RECOMMENDATION = Gauge(
    "weather_lawn_recommendation",
    "One-hot lawn recommendation state",
    ["recommendation"],
)


def record_request(route: str, method: str, status_code: int, duration_seconds: float) -> None:
    REQUESTS_TOTAL.labels(route=route, method=method, status=str(status_code)).inc()
    REQUEST_DURATION_SECONDS.labels(route=route, method=method).observe(duration_seconds)


def record_upstream(
    endpoint: str,
    *,
    success: bool,
    duration_seconds: float,
    error_type: str | None = None,
) -> None:
    result = "success" if success else "error"
    UPSTREAM_REQUESTS_TOTAL.labels(endpoint=endpoint, result=result).inc()
    UPSTREAM_REQUEST_DURATION_SECONDS.labels(endpoint=endpoint).observe(duration_seconds)
    if not success and error_type is not None:
        UPSTREAM_ERRORS_TOTAL.labels(endpoint=endpoint, error_type=error_type).inc()


def record_cache_hit() -> None:
    CACHE_HITS_TOTAL.inc()


def record_cache_miss() -> None:
    CACHE_MISSES_TOTAL.inc()


def set_cache_state(*, cache_age_seconds: int, last_successful_refresh: datetime | None, stale: bool) -> None:
    CACHE_AGE_SECONDS.set(cache_age_seconds)
    WEATHER_DATA_STALE.set(1 if stale else 0)

    if last_successful_refresh is None:
        LAST_SUCCESSFUL_REFRESH_TIMESTAMP_SECONDS.set(0)
        return

    ts = last_successful_refresh
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    LAST_SUCCESSFUL_REFRESH_TIMESTAMP_SECONDS.set(ts.timestamp())


def set_weather_metrics(payload: WeatherPayload) -> None:
    current = payload.current

    if current.temperature_f is not None:
        WEATHER_TEMPERATURE_F.set(current.temperature_f)
    if current.feels_like_f is not None:
        WEATHER_FEELS_LIKE_F.set(current.feels_like_f)
    if current.relative_humidity_percent is not None:
        WEATHER_HUMIDITY.set(current.relative_humidity_percent)
    if current.wind_speed_mph is not None:
        WEATHER_WIND_SPEED.set(current.wind_speed_mph)
    if current.wind_gust_mph is not None:
        WEATHER_WIND_GUST.set(current.wind_gust_mph)

    next_hour_precip = payload.hourly[0].precip_probability_percent if payload.hourly else 0
    next_day_precip = max(
        [period.precip_probability_percent or 0 for period in payload.hourly[:24]],
        default=0,
    )
    WEATHER_PRECIP.labels(period="next_1h").set(next_hour_precip or 0)
    WEATHER_PRECIP.labels(period="next_24h").set(next_day_precip)

    severity_counts: dict[str, int] = {}
    for alert in payload.alerts:
        severity = (alert.severity or "unknown").lower()
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    default_severities = ("extreme", "severe", "moderate", "minor", "unknown")
    for severity in default_severities:
        WEATHER_ACTIVE_ALERTS.labels(severity=severity).set(severity_counts.get(severity, 0))
    for severity, count in severity_counts.items():
        if severity in default_severities:
            continue
        WEATHER_ACTIVE_ALERTS.labels(severity=severity).set(count)

    WEATHER_GOLF_SCORE.set(payload.recommendations.golf.score)

    active_recommendation = payload.recommendations.lawn.recommendation
    for recommendation in ("Water", "Skip", "Delay", "Optional"):
        WEATHER_LAWN_RECOMMENDATION.labels(recommendation=recommendation).set(
            1 if recommendation == active_recommendation else 0
        )

    set_cache_state(
        cache_age_seconds=payload.metadata.cache_age_seconds,
        last_successful_refresh=payload.metadata.last_successful_refresh,
        stale=payload.metadata.stale,
    )


def render_metrics() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
