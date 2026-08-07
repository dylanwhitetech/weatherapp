import asyncio

import pytest

from weather_api.main import _weather_refresh_loop


class _StubService:
    """Minimal stand-in for WeatherService.get_dashboard_weather."""

    def __init__(self, failures: int = 0) -> None:
        self.calls = 0
        self._failures = failures

    async def get_dashboard_weather(self):
        self.calls += 1
        if self.calls <= self._failures:
            raise RuntimeError("upstream unavailable")
        return {"ok": True}


@pytest.mark.asyncio
async def test_refresh_loop_primes_cache_without_inbound_traffic():
    """The pod must refresh on its own, otherwise readiness never flips."""
    service = _StubService()

    task = asyncio.create_task(_weather_refresh_loop(service, interval_seconds=60))
    await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert service.calls >= 1

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_refresh_loop_retries_after_failure():
    """A failing upstream must not kill the loop - it retries with backoff."""
    service = _StubService(failures=1)

    task = asyncio.create_task(_weather_refresh_loop(service, interval_seconds=60))
    await asyncio.sleep(1.2)

    assert service.calls >= 2

    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
