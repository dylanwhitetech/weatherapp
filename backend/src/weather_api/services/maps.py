import asyncio
import csv
import io
import math
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from loguru import logger

from weather_api.config import Settings
from weather_api.models import (
    AirQualityObservation,
    AirQualityOverlayPayload,
    FirePoint,
    FiresOverlayPayload,
    MapLayer,
    MapLayerLegend,
    MapLegendEntry,
    MapPanel,
    ObservationMetric,
    WeatherObservationOverlayPayload,
    WeatherObservationPoint,
)


class MapLayerError(Exception):
    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class MapService:
    def __init__(self, http_client: httpx.AsyncClient, settings: Settings) -> None:
        self._http_client = http_client
        self._settings = settings
        self._rainviewer_cache: tuple[datetime, str, str, int] | None = None
        self._fires_cache: tuple[datetime, FiresOverlayPayload] | None = None
        self._air_quality_cache: tuple[datetime, AirQualityOverlayPayload] | None = None
        self._observations_cache: dict[ObservationMetric, tuple[datetime, WeatherObservationOverlayPayload]] = {}
        self._cache_lock = asyncio.Lock()

    def build_map_panel(self, generated_at: datetime) -> MapPanel:
        layer_defaults = [
            MapLayer(
                id="temperature",
                label="Temp",
                kind="observation-points",
                description="Observed station temperatures near the configured location",
                enabled=True,
                unavailable_reason=None,
                tile_url=None,
                data_url="/api/v1/maps/observations/temperature",
                source="National Weather Service Observations",
                attribution="Observation data © NOAA/NWS",
                updated_at=generated_at,
                legend=MapLayerLegend(
                    title="Temperature",
                    units="°F",
                    entries=[
                        MapLegendEntry(label="Cold", color="#2563eb"),
                        MapLegendEntry(label="Mild", color="#22c55e"),
                        MapLegendEntry(label="Warm", color="#f59e0b"),
                        MapLegendEntry(label="Hot", color="#dc2626"),
                    ],
                    note="Point markers are station observations, not a continuous heatmap.",
                ),
            ),
            MapLayer(
                id="wind",
                label="Wind",
                kind="observation-points",
                description="Observed station wind speed near the configured location",
                enabled=True,
                unavailable_reason=None,
                tile_url=None,
                data_url="/api/v1/maps/observations/wind",
                source="National Weather Service Observations",
                attribution="Observation data © NOAA/NWS",
                updated_at=generated_at,
                legend=MapLayerLegend(
                    title="Wind",
                    units="mph",
                    entries=[
                        MapLegendEntry(label="Light", color="#60a5fa"),
                        MapLegendEntry(label="Moderate", color="#eab308"),
                        MapLegendEntry(label="Strong", color="#f97316"),
                        MapLegendEntry(label="Very strong", color="#dc2626"),
                    ],
                    note="Point markers are station observations, not a continuous wind field.",
                ),
            ),
            self._tile_layer(
                layer_id="precipitation",
                label="Precip",
                description="Observed radar precipitation",
                source="RainViewer Radar",
                attribution="Radar tiles © RainViewer",
                updated_at=generated_at,
                enabled=True,
                tile_available=True,
                unavailable_reason=None,
                legend=MapLayerLegend(
                    title="Precipitation",
                    units="Reflectivity intensity",
                    entries=[
                        MapLegendEntry(label="Light rain/snow", color="#60a5fa"),
                        MapLegendEntry(label="Moderate precipitation", color="#22c55e"),
                        MapLegendEntry(label="Heavy precipitation", color="#ef4444"),
                    ],
                    note="Observed radar, not forecast model precipitation.",
                ),
            ),
            MapLayer(
                id="fires",
                label="Fires",
                kind="fires",
                description="Recent active-fire detections near the configured location",
                enabled=True,
                unavailable_reason=None,
                tile_url=None,
                data_url="/api/v1/maps/fires",
                source="NASA FIRMS (VIIRS C2, 24h)",
                attribution="Fire detections © NASA FIRMS",
                updated_at=generated_at,
                legend=MapLayerLegend(
                    title="Active fires",
                    units="Distance from configured center (km)",
                    entries=[
                        MapLegendEntry(label="Recent detection", color="#f97316"),
                        MapLegendEntry(label="Older detection", color="#a855f7"),
                    ],
                    note="Points represent satellite detections, not full fire perimeters.",
                ),
            ),
            MapLayer(
                id="air-quality",
                label="Air Quality",
                kind="air-quality",
                description="Observed AQI stations near the configured location",
                enabled=True,
                unavailable_reason=None if self._settings.airnow_api_key else "AIRNOW_API_KEY is not configured",
                tile_url=None,
                data_url="/api/v1/maps/air-quality",
                source="US EPA AirNow API",
                attribution="Air quality data © US EPA AirNow",
                updated_at=generated_at,
                legend=MapLayerLegend(
                    title="US AQI",
                    units="AQI",
                    entries=[
                        MapLegendEntry(label="Good (0-50)", color="#22c55e"),
                        MapLegendEntry(label="Moderate (51-100)", color="#eab308"),
                        MapLegendEntry(label="USG (101-150)", color="#f97316"),
                        MapLegendEntry(label="Unhealthy+ (151+)", color="#ef4444"),
                    ],
                    note="Station observations, not a continuous heatmap.",
                ),
            ),
        ]

        default_layer_id = "temperature"
        if not _layer_is_renderable(_find_layer(layer_defaults, default_layer_id)):
            for layer in layer_defaults:
                if _layer_is_renderable(layer):
                    default_layer_id = layer.id
                    break

        return MapPanel(
            default_layer_id=default_layer_id,
            cycle_seconds=self._settings.map_cycle_seconds,
            zoom=self._settings.map_default_zoom,
            overlay_opacity=self._settings.map_overlay_opacity,
            layers=layer_defaults,
        )

    async def fetch_tile(self, layer_id: str, z: int, x: int, y: int) -> tuple[bytes, str]:
        if layer_id == "precipitation":
            return await self._fetch_rainviewer_tile(z, x, y)
        raise MapLayerError(f"Unknown tile layer: {layer_id}", status_code=404)

    async def get_fires_overlay(self) -> FiresOverlayPayload:
        now = datetime.now(UTC)
        async with self._cache_lock:
            if self._fires_cache is not None:
                cached_at, payload = self._fires_cache
                if now - cached_at < timedelta(seconds=self._settings.map_cache_ttl_seconds):
                    return payload

            payload = await self._fetch_fires_overlay()
            self._fires_cache = (now, payload)
            return payload

    async def get_air_quality_overlay(self) -> AirQualityOverlayPayload:
        now = datetime.now(UTC)
        async with self._cache_lock:
            if self._air_quality_cache is not None:
                cached_at, payload = self._air_quality_cache
                if now - cached_at < timedelta(seconds=self._settings.map_cache_ttl_seconds):
                    return payload

            payload = await self._fetch_air_quality_overlay()
            self._air_quality_cache = (now, payload)
            return payload

    async def get_observation_overlay(self, metric: ObservationMetric) -> WeatherObservationOverlayPayload:
        now = datetime.now(UTC)
        async with self._cache_lock:
            cached = self._observations_cache.get(metric)
            if cached is not None:
                cached_at, payload = cached
                if now - cached_at < timedelta(seconds=self._settings.map_cache_ttl_seconds):
                    return payload

            payload = await self._fetch_observation_overlay(metric)
            self._observations_cache[metric] = (now, payload)
            return payload

    async def _fetch_observation_overlay(self, metric: ObservationMetric) -> WeatherObservationOverlayPayload:
        points_url = f"{self._settings.nws_base_url}/points/{self._settings.weather_latitude},{self._settings.weather_longitude}"
        points_payload = await self._fetch_json(points_url, source="NWS points", headers=self._nws_headers)
        stations_url = _safe_str(_safe_dict(points_payload.get("properties")).get("observationStations"))
        if not stations_url:
            raise MapLayerError("NWS points response is missing observation station URL", status_code=502)

        stations_payload = await self._fetch_json(
            stations_url,
            source="NWS stations",
            headers=self._nws_headers,
        )
        features = _safe_list(stations_payload.get("features"))
        station_rows: list[dict[str, Any]] = []
        for feature in features[: self._settings.map_observation_station_limit]:
            if not isinstance(feature, dict):
                continue
            properties = _safe_dict(feature.get("properties"))
            station_id = _safe_str(properties.get("stationIdentifier"))
            if not station_id:
                continue
            geometry = _safe_dict(feature.get("geometry"))
            coordinates = _safe_list(geometry.get("coordinates"))
            if len(coordinates) < 2:
                continue
            lon = _to_float(coordinates[0])
            lat = _to_float(coordinates[1])
            if lon is None or lat is None:
                continue
            station_rows.append(
                {
                    "station_id": station_id,
                    "station_name": _safe_str(properties.get("name")),
                    "latitude": lat,
                    "longitude": lon,
                }
            )

        observation_tasks = [self._fetch_station_latest_observation(row["station_id"]) for row in station_rows]
        observation_payloads = await asyncio.gather(*observation_tasks, return_exceptions=True)

        points: list[WeatherObservationPoint] = []
        center_lat = self._settings.weather_latitude
        center_lon = self._settings.weather_longitude

        for row, observation_payload in zip(station_rows, observation_payloads, strict=True):
            if isinstance(observation_payload, Exception):
                continue
            point = _parse_station_observation(
                observation_payload,
                metric=metric,
                station_id=row["station_id"],
                station_name=row["station_name"],
                latitude=row["latitude"],
                longitude=row["longitude"],
            )
            if point is None:
                continue
            distance_km = _haversine_km(center_lat, center_lon, point.latitude, point.longitude)
            if distance_km > 400:
                continue
            points.append(point)

        points.sort(
            key=lambda point: _haversine_km(center_lat, center_lon, point.latitude, point.longitude),
        )
        points = points[: self._settings.map_observation_point_limit]
        updated_at = max((point.observed_at for point in points if point.observed_at is not None), default=None)

        return WeatherObservationOverlayPayload(
            metric=metric,
            source="National Weather Service Observations",
            fetched_at=datetime.now(UTC),
            updated_at=updated_at,
            points=points,
        )

    async def _fetch_rainviewer_tile(self, z: int, x: int, y: int) -> tuple[bytes, str]:
        host, path, _frame_time = await self._get_rainviewer_frame()
        url = f"{host}{path}/256/{z}/{x}/{y}/2/1_1.png"
        return await self._fetch_png(url, source="RainViewer")

    async def _fetch_station_latest_observation(self, station_id: str) -> dict[str, Any]:
        url = f"{self._settings.nws_base_url}/stations/{station_id}/observations/latest"
        return await self._fetch_json(url, source="NWS observation", headers=self._nws_headers)

    async def _fetch_air_quality_overlay(self) -> AirQualityOverlayPayload:
        key = self._settings.airnow_api_key
        if not key:
            raise MapLayerError("AirNow air quality layer is not configured", status_code=503)

        url = f"{self._settings.airnow_base_url.rstrip('/')}/aq/observation/latLong/current/"
        params = {
            "format": "application/json",
            "latitude": self._settings.weather_latitude,
            "longitude": self._settings.weather_longitude,
            "distance": self._settings.airnow_search_distance_miles,
            "API_KEY": key,
        }

        try:
            response = await self._http_client.get(
                url,
                params=params,
                timeout=self._settings.map_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as error:
            logger.warning("AirNow fetch failed", error_type=error.__class__.__name__)
            raise MapLayerError("Unable to load air quality observations", status_code=502) from error
        except ValueError as error:
            raise MapLayerError("AirNow response was not valid JSON", status_code=502) from error

        if not isinstance(payload, list):
            raise MapLayerError("AirNow response did not contain observation rows", status_code=502)

        observations: list[AirQualityObservation] = []
        for row in payload:
            parsed = _parse_airnow_row(
                row,
                center_lat=self._settings.weather_latitude,
                center_lon=self._settings.weather_longitude,
            )
            if parsed is None:
                continue
            observations.append(parsed)

        observations.sort(key=lambda item: item.aqi, reverse=True)
        observations = observations[: self._settings.airnow_max_observations]

        updated_at = max((item.observed_at for item in observations if item.observed_at is not None), default=None)
        return AirQualityOverlayPayload(
            source="US EPA AirNow API",
            fetched_at=datetime.now(UTC),
            updated_at=updated_at,
            observations=observations,
        )

    async def _get_rainviewer_frame(self) -> tuple[str, str, int]:
        now = datetime.now(UTC)
        async with self._cache_lock:
            if self._rainviewer_cache is not None:
                cached_at, host, path, frame_time = self._rainviewer_cache
                if now - cached_at < timedelta(seconds=self._settings.map_cache_ttl_seconds):
                    return host, path, frame_time

            response = await self._http_client.get(
                self._settings.rainviewer_api_url,
                timeout=self._settings.map_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise MapLayerError("RainViewer metadata response was not valid JSON", status_code=502)

            host = _safe_str(payload.get("host"))
            radar = _safe_dict(payload.get("radar"))
            past = _safe_list(radar.get("past"))
            frame = _safe_dict(past[-1]) if past else {}
            path = _safe_str(frame.get("path"))
            frame_time = _to_int(frame.get("time")) or int(now.timestamp())

            if not host or not path:
                raise MapLayerError("RainViewer metadata is missing tile host/path", status_code=502)

            self._rainviewer_cache = (now, host, path, frame_time)
            return host, path, frame_time

    async def _fetch_png(self, url: str, *, source: str) -> tuple[bytes, str]:
        try:
            response = await self._http_client.get(url, timeout=self._settings.map_timeout_seconds)
            response.raise_for_status()
        except httpx.HTTPError as error:
            logger.warning("Map tile fetch failed", source=source, error_type=error.__class__.__name__)
            raise MapLayerError(f"{source} tile request failed", status_code=502) from error

        content_type = response.headers.get("content-type", "image/png")
        return response.content, content_type

    async def _fetch_json(
        self,
        url: str,
        *,
        source: str,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        try:
            response = await self._http_client.get(
                url,
                headers=headers,
                timeout=self._settings.map_timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as error:
            logger.warning("Map JSON fetch failed", source=source, error_type=error.__class__.__name__)
            raise MapLayerError(f"{source} request failed", status_code=502) from error
        except ValueError as error:
            raise MapLayerError(f"{source} response was not valid JSON", status_code=502) from error

        if not isinstance(payload, dict):
            raise MapLayerError(f"{source} response was not a JSON object", status_code=502)
        return payload

    @property
    def _nws_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/geo+json, application/json",
            "User-Agent": self._settings.nws_user_agent,
        }

    async def _fetch_fires_overlay(self) -> FiresOverlayPayload:
        now = datetime.now(UTC)
        try:
            snpp_csv, noaa20_csv = await asyncio.gather(
                self._fetch_text(self._settings.firms_viirs_snpp_csv_url),
                self._fetch_text(self._settings.firms_viirs_noaa20_csv_url),
            )
        except httpx.HTTPError as error:
            logger.warning("FIRMS fetch failed", error_type=error.__class__.__name__)
            raise MapLayerError("Unable to load fire detection data", status_code=502) from error

        center_lat = self._settings.weather_latitude
        center_lon = self._settings.weather_longitude
        radius_km = self._settings.firms_search_radius_km

        points = _parse_firms_csv(
            snpp_csv,
            satellite="Suomi NPP",
            center_lat=center_lat,
            center_lon=center_lon,
            radius_km=radius_km,
        )
        points.extend(
            _parse_firms_csv(
                noaa20_csv,
                satellite="NOAA-20",
                center_lat=center_lat,
                center_lon=center_lon,
                radius_km=radius_km,
            )
        )

        points.sort(
            key=lambda point: (
                point.acquired_at or datetime(1970, 1, 1, tzinfo=UTC),
                -point.distance_km,
            ),
            reverse=True,
        )
        points = points[: self._settings.firms_max_points]
        updated_at = max((point.acquired_at for point in points if point.acquired_at is not None), default=None)

        return FiresOverlayPayload(
            source="NASA FIRMS (VIIRS C2 Global 24h)",
            fetched_at=now,
            updated_at=updated_at,
            points=points,
        )

    async def _fetch_text(self, url: str) -> str:
        response = await self._http_client.get(url, timeout=self._settings.map_timeout_seconds)
        response.raise_for_status()
        return response.text

    def _tile_layer(
        self,
        *,
        layer_id: str,
        label: str,
        description: str,
        source: str,
        attribution: str,
        updated_at: datetime | None,
        enabled: bool,
        tile_available: bool,
        unavailable_reason: str | None,
        legend: MapLayerLegend,
    ) -> MapLayer:
        return MapLayer(
            id=layer_id,
            label=label,
            kind="tile",
            description=description,
            enabled=enabled,
            unavailable_reason=None if tile_available else unavailable_reason,
            tile_url=f"/api/v1/maps/tiles/{layer_id}/{{z}}/{{x}}/{{y}}.png" if tile_available else None,
            data_url=None,
            source=source,
            attribution=attribution,
            updated_at=updated_at,
            legend=legend,
        )


def _parse_firms_csv(
    payload: str,
    *,
    satellite: str,
    center_lat: float,
    center_lon: float,
    radius_km: float,
) -> list[FirePoint]:
    points: list[FirePoint] = []
    reader = csv.DictReader(io.StringIO(payload))
    for row in reader:
        latitude = _to_float(row.get("latitude"))
        longitude = _to_float(row.get("longitude"))
        if latitude is None or longitude is None:
            continue

        distance_km = _haversine_km(center_lat, center_lon, latitude, longitude)
        if distance_km > radius_km:
            continue

        acquired_at = _parse_firms_datetime(row.get("acq_date"), row.get("acq_time"))
        points.append(
            FirePoint(
                latitude=latitude,
                longitude=longitude,
                distance_km=round(distance_km, 1),
                confidence=_safe_str(row.get("confidence")),
                brightness=_to_float(row.get("bright_ti4") or row.get("brightness")),
                acquired_at=acquired_at,
                satellite=satellite,
            )
        )
    return points


def _parse_station_observation(
    payload: dict[str, Any],
    *,
    metric: ObservationMetric,
    station_id: str,
    station_name: str | None,
    latitude: float,
    longitude: float,
) -> WeatherObservationPoint | None:
    properties = _safe_dict(payload.get("properties"))
    observed_at = _parse_iso_datetime(_safe_str(properties.get("timestamp")))

    if metric == "temperature":
        temperature_c = _nested_numeric(properties, "temperature", "value")
        temperature_f = _c_to_f(temperature_c)
        if temperature_f is None:
            return None
        return WeatherObservationPoint(
            latitude=latitude,
            longitude=longitude,
            value=temperature_f,
            unit="°F",
            station_id=station_id,
            station_name=station_name,
            wind_direction=None,
            observed_at=observed_at,
        )

    if metric == "wind":
        wind_speed_mps = _nested_numeric(properties, "windSpeed", "value")
        wind_speed_mph = _mps_to_mph(wind_speed_mps)
        if wind_speed_mph is None:
            return None
        wind_deg = _nested_numeric(properties, "windDirection", "value")
        wind_direction = _degrees_to_cardinal(wind_deg)
        return WeatherObservationPoint(
            latitude=latitude,
            longitude=longitude,
            value=wind_speed_mph,
            unit="mph",
            station_id=station_id,
            station_name=station_name,
            wind_direction=wind_direction,
            observed_at=observed_at,
        )

    return None


def _parse_airnow_row(
    row: Any,
    *,
    center_lat: float,
    center_lon: float,
) -> AirQualityObservation | None:
    if not isinstance(row, dict):
        return None

    latitude = _to_float(row.get("Latitude"))
    longitude = _to_float(row.get("Longitude"))
    aqi = _to_int(row.get("AQI"))
    category = _safe_str(_safe_dict(row.get("Category")).get("Name"))
    pollutant = _safe_str(row.get("ParameterName"))
    reporting_area = _safe_str(row.get("ReportingArea"))

    if latitude is None or longitude is None or aqi is None:
        return None
    if category is None or pollutant is None or reporting_area is None:
        return None

    observed_at = _parse_airnow_datetime(
        _safe_str(row.get("DateObserved")),
        _to_int(row.get("HourObserved")),
    )
    distance_miles = _haversine_km(center_lat, center_lon, latitude, longitude) * 0.621371

    return AirQualityObservation(
        latitude=latitude,
        longitude=longitude,
        aqi=aqi,
        category=category,
        pollutant=pollutant,
        reporting_area=reporting_area,
        state_code=_safe_str(row.get("StateCode")),
        distance_miles=round(distance_miles, 1),
        observed_at=observed_at,
    )


def _parse_airnow_datetime(date_observed: str | None, hour_observed: int | None) -> datetime | None:
    if date_observed is None or hour_observed is None:
        return None

    parsed_parts = _parse_airnow_date_parts(date_observed)
    if parsed_parts is None:
        return None

    if hour_observed < 0 or hour_observed > 23:
        return None

    try:
        return datetime(
            parsed_parts[0],
            parsed_parts[1],
            parsed_parts[2],
            hour_observed,
            0,
            tzinfo=UTC,
        )
    except ValueError:
        return None


def _parse_airnow_date_parts(date_observed: str) -> tuple[int, int, int] | None:
    if "-" in date_observed:
        parts = date_observed.split("-")
        if len(parts) != 3:
            return None
        try:
            return int(parts[0]), int(parts[1]), int(parts[2])
        except ValueError:
            return None

    if "/" in date_observed:
        parts = date_observed.split("/")
        if len(parts) != 3:
            return None
        try:
            return int(parts[2]), int(parts[0]), int(parts[1])
        except ValueError:
            return None

    return None


def _parse_firms_datetime(acq_date: Any, acq_time: Any) -> datetime | None:
    if not isinstance(acq_date, str):
        return None
    if not isinstance(acq_time, str):
        return None

    normalized_time = acq_time.strip().zfill(4)
    if len(normalized_time) != 4 or not normalized_time.isdigit():
        return None

    date_parts = acq_date.split("-")
    if len(date_parts) != 3:
        return None

    try:
        year = int(date_parts[0])
        month = int(date_parts[1])
        day = int(date_parts[2])
        hour = int(normalized_time[:2])
        minute = int(normalized_time[2:])
    except ValueError:
        return None

    try:
        return datetime(year, month, day, hour, minute, tzinfo=UTC)
    except ValueError:
        return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def _nested_numeric(payload: dict[str, Any], outer_key: str, inner_key: str) -> float | None:
    outer = _safe_dict(payload.get(outer_key))
    return _to_float(outer.get(inner_key))


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _c_to_f(celsius: float | None) -> float | None:
    if celsius is None:
        return None
    return round((celsius * 9 / 5) + 32, 1)


def _mps_to_mph(mps: float | None) -> float | None:
    if mps is None:
        return None
    return round(mps * 2.23694, 1)


def _degrees_to_cardinal(degrees: float | None) -> str | None:
    if degrees is None:
        return None
    labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = int(((degrees + 22.5) % 360) / 45)
    return labels[index]


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
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _to_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _find_layer(layers: list[MapLayer], layer_id: str) -> MapLayer | None:
    for layer in layers:
        if layer.id == layer_id:
            return layer
    return None


def _layer_is_renderable(layer: MapLayer | None) -> bool:
    if layer is None:
        return False
    if not layer.enabled:
        return False
    if layer.kind == "tile":
        return layer.tile_url is not None
    return layer.data_url is not None
