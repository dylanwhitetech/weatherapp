import asyncio
import random
import time
from typing import Any
from urllib.parse import urlparse

import httpx

from weather_api.config import Settings
from weather_api.telemetry import record_upstream


class NwsClient:
    def __init__(self, http_client: httpx.AsyncClient, settings: Settings) -> None:
        self._http_client = http_client
        self._settings = settings

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/geo+json, application/json",
            "User-Agent": self._settings.nws_user_agent,
        }

    async def _request_json(self, url: str, endpoint_name: str) -> dict[str, Any]:
        attempts = self._settings.nws_max_retries + 1
        backoff = self._settings.nws_backoff_seconds

        for attempt in range(attempts):
            started = time.perf_counter()
            try:
                response = await self._http_client.get(
                    url,
                    headers=self._headers,
                    timeout=self._settings.nws_timeout_seconds,
                )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("NWS response was not a JSON object")

                record_upstream(
                    endpoint_name,
                    success=True,
                    duration_seconds=time.perf_counter() - started,
                )
                return payload
            except (httpx.HTTPError, ValueError) as error:
                record_upstream(
                    endpoint_name,
                    success=False,
                    duration_seconds=time.perf_counter() - started,
                    error_type=error.__class__.__name__,
                )
                if attempt == attempts - 1:
                    raise
                await asyncio.sleep(backoff * (2**attempt) + random.uniform(0, 0.1))

        raise RuntimeError("Unreachable retry state")

    async def fetch_raw_weather(self, latitude: float, longitude: float) -> dict[str, Any]:
        points_url = f"{self._settings.nws_base_url}/points/{latitude},{longitude}"
        points_payload = await self._request_json(points_url, "points")
        points_properties = points_payload.get("properties", {})

        forecast_url = str(points_properties.get("forecast"))
        hourly_url = str(points_properties.get("forecastHourly"))
        stations_url = str(points_properties.get("observationStations"))
        forecast_zone_url = str(points_properties.get("forecastZone"))

        if not forecast_url or not hourly_url or not stations_url:
            raise ValueError("NWS points response did not include required endpoint URLs")

        forecast_payload, hourly_payload, station_payload = await asyncio.gather(
            self._request_json(forecast_url, "forecast"),
            self._request_json(hourly_url, "hourly"),
            self._fetch_latest_observation(stations_url),
        )

        alerts_payload = {"features": []}
        zone_id = _extract_zone_id(forecast_zone_url)
        if zone_id is not None:
            alerts_url = f"{self._settings.nws_base_url}/alerts/active?zone={zone_id}"
            alerts_payload = await self._request_json(alerts_url, "alerts")

        return {
            "points": points_payload,
            "forecast": forecast_payload,
            "hourly": hourly_payload,
            "observation": station_payload,
            "alerts": alerts_payload,
        }

    async def _fetch_latest_observation(self, stations_url: str) -> dict[str, Any]:
        stations_payload = await self._request_json(stations_url, "stations")
        features = stations_payload.get("features", [])
        if not isinstance(features, list) or len(features) == 0:
            raise ValueError("NWS stations response did not include station features")

        station_identifier = None
        first_feature = features[0]
        if isinstance(first_feature, dict):
            props = first_feature.get("properties", {})
            if isinstance(props, dict):
                station_identifier = props.get("stationIdentifier")

        if not isinstance(station_identifier, str) or station_identifier == "":
            raise ValueError("Station identifier missing from NWS station feature")

        observation_url = f"{self._settings.nws_base_url}/stations/{station_identifier}/observations/latest"
        return await self._request_json(observation_url, "observation")


def _extract_zone_id(forecast_zone_url: str | None) -> str | None:
    if not forecast_zone_url:
        return None
    parsed = urlparse(forecast_zone_url)
    segment = parsed.path.rstrip("/").split("/")[-1]
    return segment or None
