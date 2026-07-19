from weather_api.models import Alert, CurrentConditions, ForecastPeriod, LawnRecommendation


DISCLAIMER = (
    "Estimate only; adjust for soil, grass type, shade, and local watering restrictions."
)


def calculate_lawn_recommendation(
    hourly: list[ForecastPeriod], current: CurrentConditions, alerts: list[Alert]
) -> LawnRecommendation:
    horizon = hourly[:24]
    max_precip = max((period.precip_probability_percent or 0) for period in horizon) if horizon else 0
    max_temp = max((period.temperature_f or current.temperature_f or 0) for period in horizon) if horizon else (
        current.temperature_f or 0
    )
    max_wind = max((period.wind_gust_mph or period.wind_speed_mph or 0) for period in horizon) if horizon else (
        current.wind_gust_mph or current.wind_speed_mph or 0
    )
    min_humidity = current.relative_humidity_percent if current.relative_humidity_percent is not None else 35

    severe_alert = any(
        _contains_blocking_alert((alert.event or "") + " " + (alert.headline or "")) for alert in alerts
    )

    reasons: list[str] = []
    if max_precip >= 60 or severe_alert:
        reasons.append("Meaningful precipitation or weather hazard is likely")
        recommendation = "Skip"
        confidence = "high"
        summary = "Rain risk is high enough that watering should be skipped."
        suggested_time = "N/A"
    elif max_precip >= 35 or max_wind >= 25:
        reasons.append("Rain chance or wind could reduce watering effectiveness")
        recommendation = "Delay"
        confidence = "medium"
        summary = "Delay watering until the next calmer/drier window."
        suggested_time = "Early morning after risk passes"
    elif max_temp >= 88 and max_precip < 20 and min_humidity <= 35:
        reasons.extend(
            [
                "Hot and dry conditions are expected",
                "Rain probability is low",
            ]
        )
        recommendation = "Water"
        confidence = "medium"
        summary = "Hot, dry conditions suggest watering is likely needed."
        suggested_time = "Early morning"
    else:
        reasons.append("Forecast does not strongly support watering or skipping")
        recommendation = "Optional"
        confidence = "low"
        summary = "Conditions are moderate; watering is optional."
        suggested_time = "Early morning"

    return LawnRecommendation(
        recommendation=recommendation,
        confidence=confidence,
        suggested_time=suggested_time,
        summary=summary,
        reasons=reasons,
        disclaimer=DISCLAIMER,
    )


def _contains_blocking_alert(text: str) -> bool:
    lowered = text.lower()
    keywords = ("flood", "thunderstorm", "tornado", "high wind", "hail")
    return any(keyword in lowered for keyword in keywords)
