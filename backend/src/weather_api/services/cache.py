import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Awaitable, Callable

from weather_api.models import WeatherMetadata, WeatherPayload
from weather_api.telemetry import record_cache_hit, record_cache_miss, set_cache_state


class WeatherDataUnavailable(Exception):
    pass


@dataclass
class CacheStatus:
    has_data: bool
    age_seconds: int
    stale: bool
    last_successful_refresh: datetime | None


class WeatherCache:
    def __init__(self, ttl_seconds: int, stale_max_seconds: int) -> None:
        self._ttl_seconds = ttl_seconds
        self._stale_max_seconds = stale_max_seconds
        self._payload: WeatherPayload | None = None
        self._last_successful_refresh: datetime | None = None
        self._refresh_task: asyncio.Task[WeatherPayload] | None = None
        self._lock = asyncio.Lock()

    async def get_weather(
        self, fetch_fresh: Callable[[], Awaitable[WeatherPayload]]
    ) -> WeatherPayload:
        if self._is_fresh():
            record_cache_hit()
            return self._annotated_payload(stale=False, status_message=None)

        record_cache_miss()
        refresh_task = await self._get_or_create_refresh_task(fetch_fresh)
        try:
            payload = await refresh_task
            return self._annotated_payload(
                stale=False,
                status_message=None,
                generated_override=payload.metadata.generated_at,
            )
        except Exception as error:
            status = self.get_status()
            if status.has_data and status.age_seconds <= self._stale_max_seconds:
                return self._annotated_payload(
                    stale=True,
                    status_message=f"Serving stale weather data due to upstream error: {error.__class__.__name__}",
                )
            raise WeatherDataUnavailable("No usable weather data is available") from error

    def get_status(self) -> CacheStatus:
        age_seconds = self._age_seconds()
        stale = self._payload is not None and age_seconds > self._ttl_seconds
        return CacheStatus(
            has_data=self._payload is not None,
            age_seconds=age_seconds,
            stale=stale,
            last_successful_refresh=self._last_successful_refresh,
        )

    def _is_fresh(self) -> bool:
        return self._payload is not None and self._age_seconds() <= self._ttl_seconds

    def _age_seconds(self) -> int:
        if self._last_successful_refresh is None:
            return 0
        now = datetime.now(timezone.utc)
        return max(0, int((now - self._last_successful_refresh).total_seconds()))

    async def _get_or_create_refresh_task(
        self, fetch_fresh: Callable[[], Awaitable[WeatherPayload]]
    ) -> asyncio.Task[WeatherPayload]:
        async with self._lock:
            if self._is_fresh():
                return asyncio.create_task(self._return_cached())
            if self._refresh_task is not None and not self._refresh_task.done():
                return self._refresh_task

            self._refresh_task = asyncio.create_task(self._refresh(fetch_fresh))
            return self._refresh_task

    async def _refresh(self, fetch_fresh: Callable[[], Awaitable[WeatherPayload]]) -> WeatherPayload:
        payload = await fetch_fresh()
        self._payload = payload
        self._last_successful_refresh = payload.metadata.last_successful_refresh

        set_cache_state(
            cache_age_seconds=0,
            last_successful_refresh=self._last_successful_refresh,
            stale=False,
        )
        return payload

    async def _return_cached(self) -> WeatherPayload:
        if self._payload is None:
            raise WeatherDataUnavailable("No cache payload exists")
        return self._payload

    def _annotated_payload(
        self,
        *,
        stale: bool,
        status_message: str | None,
        generated_override: datetime | None = None,
    ) -> WeatherPayload:
        if self._payload is None:
            raise WeatherDataUnavailable("No cache payload exists")

        age_seconds = self._age_seconds()
        generated_at = generated_override or datetime.now(timezone.utc)
        metadata = WeatherMetadata(
            source=self._payload.metadata.source,
            generated_at=generated_at,
            last_successful_refresh=self._last_successful_refresh,
            stale=stale,
            cache_age_seconds=age_seconds,
            status_message=status_message,
        )

        set_cache_state(
            cache_age_seconds=age_seconds,
            last_successful_refresh=self._last_successful_refresh,
            stale=stale,
        )

        return self._payload.model_copy(update={"metadata": metadata})
