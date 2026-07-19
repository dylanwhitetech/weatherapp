from datetime import datetime, timezone

import pytest

from weather_api.models import (
    CurrentConditions,
    GolfBestWindow,
    GolfRecommendation,
    LawnRecommendation,
    Location,
    Recommendations,
    WeatherMetadata,
    WeatherPayload,
)
from weather_api.services.cache import WeatherCache, WeatherDataUnavailable


def _payload() -> WeatherPayload:
    now = datetime.now(timezone.utc)
    return WeatherPayload(
        location=Location(
            name="Walla Walla, WA",
            latitude=46.0646,
            longitude=-118.3430,
            timezone="America/Los_Angeles",
        ),
        current=CurrentConditions(),
        hourly=[],
        daily=[],
        alerts=[],
        recommendations=Recommendations(
            golf=GolfRecommendation(
                score=75,
                label="Good",
                best_window=GolfBestWindow(start=now, end=now),
                summary="Good conditions",
                reasons=["Dry"],
                limited_data=False,
            ),
            lawn=LawnRecommendation(
                recommendation="Optional",
                confidence="low",
                suggested_time="Early morning",
                summary="Mild conditions",
                reasons=["No strong signal"],
                disclaimer="Estimate only",
            ),
        ),
        metadata=WeatherMetadata(
            generated_at=now,
            last_successful_refresh=now,
            stale=False,
            cache_age_seconds=0,
        ),
    )


@pytest.mark.asyncio
async def test_cache_reuses_fresh_data() -> None:
    cache = WeatherCache(ttl_seconds=600, stale_max_seconds=3600)
    calls = 0

    async def fetcher() -> WeatherPayload:
        nonlocal calls
        calls += 1
        return _payload()

    await cache.get_weather(fetcher)
    await cache.get_weather(fetcher)
    assert calls == 1


@pytest.mark.asyncio
async def test_cache_raises_when_no_data_and_fetch_fails() -> None:
    cache = WeatherCache(ttl_seconds=1, stale_max_seconds=1)

    async def fetcher() -> WeatherPayload:
        raise RuntimeError("upstream down")

    with pytest.raises(WeatherDataUnavailable):
        await cache.get_weather(fetcher)
