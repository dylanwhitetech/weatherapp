from datetime import datetime, timedelta, timezone

from weather_api.models import Alert, CurrentConditions, ForecastPeriod
from weather_api.services.golf import calculate_golf_recommendation
from weather_api.services.lawn import calculate_lawn_recommendation


def _hour_period(*, offset_hours: int, precip: float, temp: float, wind: float, condition: str) -> ForecastPeriod:
    start = datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc) + timedelta(hours=offset_hours)
    end = start + timedelta(hours=1)
    return ForecastPeriod(
        start=start,
        end=end,
        name=f"H+{offset_hours}",
        is_daytime=True,
        temperature_f=temp,
        wind_speed_mph=wind,
        wind_gust_mph=wind + 3,
        precip_probability_percent=precip,
        conditions=condition,
        icon_url=None,
    )


def test_golf_recommendation_prefers_good_window() -> None:
    periods = [
        _hour_period(offset_hours=0, precip=10, temp=79, wind=8, condition="Sunny"),
        _hour_period(offset_hours=1, precip=15, temp=81, wind=9, condition="Sunny"),
        _hour_period(offset_hours=2, precip=80, temp=77, wind=16, condition="Rain Showers"),
    ]
    recommendation = calculate_golf_recommendation(periods, alerts=[])

    assert recommendation.score >= 70
    assert recommendation.label in {"Excellent", "Good"}
    assert recommendation.best_window.start is not None
    assert len(recommendation.reasons) >= 1


def test_golf_recommendation_handles_severe_alert() -> None:
    periods = [_hour_period(offset_hours=0, precip=5, temp=75, wind=8, condition="Clear")]
    alerts = [
        Alert(
            id="alert-1",
            event="Severe Thunderstorm Warning",
            severity="Severe",
            headline="Severe Thunderstorm Warning",
            description=None,
            effective=None,
            expires=None,
            status="Actual",
        )
    ]
    recommendation = calculate_golf_recommendation(periods, alerts)
    assert recommendation.score == 0
    assert recommendation.label == "Avoid"


def test_lawn_recommendation_delay_when_rain_risk_is_moderate() -> None:
    periods = [
        _hour_period(offset_hours=0, precip=45, temp=88, wind=6, condition="Partly Cloudy"),
        _hour_period(offset_hours=1, precip=40, temp=90, wind=7, condition="Cloudy"),
    ]
    current = CurrentConditions(
        observed_at=None,
        temperature_f=86,
        feels_like_f=86,
        relative_humidity_percent=30,
        wind_speed_mph=5,
        wind_gust_mph=6,
        wind_direction="S",
        conditions="Dry",
        icon_url=None,
    )

    recommendation = calculate_lawn_recommendation(periods, current=current, alerts=[])
    assert recommendation.recommendation == "Delay"
    assert recommendation.confidence in {"medium", "high"}


def test_lawn_recommendation_water_when_hot_and_dry() -> None:
    periods = [
        _hour_period(offset_hours=0, precip=5, temp=92, wind=8, condition="Sunny"),
        _hour_period(offset_hours=1, precip=10, temp=94, wind=9, condition="Sunny"),
    ]
    current = CurrentConditions(
        observed_at=None,
        temperature_f=90,
        feels_like_f=92,
        relative_humidity_percent=25,
        wind_speed_mph=7,
        wind_gust_mph=10,
        wind_direction="SW",
        conditions="Hot",
        icon_url=None,
    )

    recommendation = calculate_lawn_recommendation(periods, current=current, alerts=[])
    assert recommendation.recommendation == "Water"
