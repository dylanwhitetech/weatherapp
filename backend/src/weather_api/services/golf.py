from dataclasses import dataclass

from weather_api.models import Alert, ForecastPeriod, GolfBestWindow, GolfLabel, GolfRecommendation


@dataclass
class HourScore:
    period: ForecastPeriod
    score: int
    reasons: list[str]
    limited_data: bool


def calculate_golf_recommendation(hourly: list[ForecastPeriod], alerts: list[Alert]) -> GolfRecommendation:
    severe_alert_active = any(
        _contains_hazard((alert.event or "") + " " + (alert.headline or ""))
        for alert in alerts
    )
    if severe_alert_active:
        return GolfRecommendation(
            score=0,
            label="Avoid",
            best_window=GolfBestWindow(),
            summary="Hazardous weather alerts are active.",
            reasons=["Severe weather alert in effect"],
            limited_data=False,
        )

    candidates = [period for period in hourly[:24] if period.is_daytime]
    if len(candidates) == 0:
        return GolfRecommendation(
            score=0,
            label="Avoid",
            best_window=GolfBestWindow(),
            summary="No daylight forecast windows are currently available.",
            reasons=["No playable daylight forecast window found"],
            limited_data=True,
        )

    hour_scores = [_score_hour(period) for period in candidates]
    best_window = _select_best_window(hour_scores)

    score = round(best_window.score)
    label = _label_for_score(score)
    reasons = best_window.reasons[:3] if len(best_window.reasons) > 0 else ["Weather conditions are mixed"]

    return GolfRecommendation(
        score=score,
        label=label,
        best_window=GolfBestWindow(
            start=best_window.period.start,
            end=best_window.period.end,
        ),
        summary=_build_summary(label),
        reasons=reasons,
        limited_data=best_window.limited_data,
    )


def _score_hour(period: ForecastPeriod) -> HourScore:
    score = 100
    reasons: list[str] = []
    limited_data = False

    conditions = (period.conditions or "").lower()
    if _contains_hazard(conditions):
        return HourScore(
            period=period,
            score=0,
            reasons=["Severe thunderstorm/tornado risk"],
            limited_data=False,
        )

    precip = period.precip_probability_percent
    if precip is None:
        limited_data = True
    elif precip >= 70:
        score -= 40
        reasons.append("High rain probability")
    elif precip >= 40:
        score -= 20
        reasons.append("Moderate rain probability")
    elif precip >= 20:
        score -= 8
        reasons.append("Slight rain chance")
    else:
        reasons.append("Low rain probability")

    gust = period.wind_gust_mph
    if gust is None:
        limited_data = True
    elif gust >= 35:
        score -= 35
        reasons.append("Very strong wind gusts")
    elif gust >= 25:
        score -= 20
        reasons.append("Wind gusts may affect play")

    wind = period.wind_speed_mph
    if wind is None:
        limited_data = True
    elif wind >= 20:
        score -= 15
        reasons.append("Sustained wind is high")
    elif wind <= 12:
        reasons.append("Manageable wind")

    temp = period.temperature_f
    if temp is None:
        limited_data = True
    elif temp > 100:
        score -= 35
        reasons.append("Dangerous heat")
    elif temp >= 95:
        score -= 20
        reasons.append("Very hot")
    elif temp >= 90:
        score -= 10
        reasons.append("Hot afternoon")
    elif temp < 40:
        score -= 25
        reasons.append("Too cold")
    elif temp < 50:
        score -= 10
        reasons.append("Cool conditions")
    elif 65 <= temp <= 85:
        reasons.append("Comfortable temperature")

    score = max(0, min(100, score))
    return HourScore(period=period, score=score, reasons=reasons, limited_data=limited_data)


def _select_best_window(scores: list[HourScore]) -> HourScore:
    # Start with the best single hour then improve with 2-3 hour windows.
    best = max(scores, key=lambda item: item.score)
    best_window_score = best.score
    best_reasons = list(best.reasons)
    best_limited = best.limited_data
    best_period = best.period

    for window_size in (2, 3):
        for index in range(0, len(scores) - window_size + 1):
            chunk = scores[index : index + window_size]
            avg = sum(item.score for item in chunk) / window_size
            if avg > best_window_score:
                best_window_score = avg
                best_reasons = _dedupe_reasons([reason for item in chunk for reason in item.reasons])
                best_limited = any(item.limited_data for item in chunk)
                best_period = ForecastPeriod(
                    start=chunk[0].period.start,
                    end=chunk[-1].period.end,
                    name=f"{window_size}-hour window",
                    is_daytime=True,
                    temperature_f=chunk[0].period.temperature_f,
                    wind_speed_mph=chunk[0].period.wind_speed_mph,
                    wind_gust_mph=chunk[0].period.wind_gust_mph,
                    precip_probability_percent=chunk[0].period.precip_probability_percent,
                    conditions=chunk[0].period.conditions,
                    icon_url=chunk[0].period.icon_url,
                )

    return HourScore(
        period=best_period,
        score=round(best_window_score),
        reasons=best_reasons,
        limited_data=best_limited,
    )


def _label_for_score(score: int) -> GolfLabel:
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 50:
        return "Playable"
    if score >= 25:
        return "Poor"
    return "Avoid"


def _build_summary(label: GolfLabel) -> str:
    summaries: dict[GolfLabel, str] = {
        "Excellent": "Great weather window for a round of golf.",
        "Good": "Solid conditions with a few manageable tradeoffs.",
        "Playable": "Playable, but expect at least one weather constraint.",
        "Poor": "Conditions are likely uncomfortable or disruptive.",
        "Avoid": "Weather risks are high and play is not advised.",
    }
    return summaries[label]


def _contains_hazard(text: str) -> bool:
    lowered = text.lower()
    hazard_keywords = ("tornado", "severe thunderstorm", "thunderstorm warning")
    return any(keyword in lowered for keyword in hazard_keywords)


def _dedupe_reasons(reasons: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        ordered.append(reason)
    return ordered
