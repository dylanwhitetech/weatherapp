from datetime import UTC, datetime

from weather_api.config import Settings
from weather_api.services.maps import (
    MapService,
    _parse_airnow_row,
    _parse_firms_csv,
    _parse_station_observation,
)


def test_build_map_panel_marks_keyed_layers_unavailable_without_keys() -> None:
    settings = Settings(_env_file=None, AIRNOW_API_KEY=None)
    map_service = MapService(_NoopHttpClient(), settings)  # type: ignore[arg-type]

    panel = map_service.build_map_panel(datetime.now(UTC))
    by_id = {layer.id: layer for layer in panel.layers}

    assert by_id["temperature"].enabled is True
    assert by_id["temperature"].tile_url is None
    assert by_id["temperature"].data_url == "/api/v1/maps/observations/temperature"
    assert by_id["temperature"].unavailable_reason is None
    assert by_id["wind"].enabled is True
    assert by_id["wind"].tile_url is None
    assert by_id["wind"].data_url == "/api/v1/maps/observations/wind"
    assert by_id["wind"].unavailable_reason is None
    assert by_id["air-quality"].enabled is True
    assert by_id["air-quality"].tile_url is None
    assert by_id["air-quality"].data_url == "/api/v1/maps/air-quality"
    assert by_id["air-quality"].unavailable_reason == "AIRNOW_API_KEY is not configured"
    assert by_id["precipitation"].enabled is True
    assert by_id["precipitation"].tile_url is not None
    assert by_id["fires"].enabled is True


def test_build_map_panel_enables_keyed_layers_when_keys_exist() -> None:
    settings = Settings(
        AIRNOW_API_KEY="test-airnow-key",
    )
    map_service = MapService(_NoopHttpClient(), settings)  # type: ignore[arg-type]

    panel = map_service.build_map_panel(datetime.now(UTC))
    by_id = {layer.id: layer for layer in panel.layers}

    assert by_id["temperature"].enabled is True
    assert by_id["temperature"].tile_url is None
    assert by_id["temperature"].data_url == "/api/v1/maps/observations/temperature"
    assert by_id["temperature"].unavailable_reason is None
    assert by_id["wind"].enabled is True
    assert by_id["wind"].tile_url is None
    assert by_id["wind"].data_url == "/api/v1/maps/observations/wind"
    assert by_id["air-quality"].enabled is True
    assert by_id["air-quality"].tile_url is None
    assert by_id["air-quality"].data_url == "/api/v1/maps/air-quality"
    assert by_id["air-quality"].unavailable_reason is None


def test_parse_firms_csv_filters_to_nearby_points() -> None:
    payload = (
        "latitude,longitude,bright_ti4,confidence,acq_date,acq_time\n"
        "46.0646,-118.3430,330.2,high,2026-07-27,1945\n"
        "35.0000,-100.0000,325.1,nominal,2026-07-27,1955"
    )

    points = _parse_firms_csv(
        payload,
        satellite="Suomi NPP",
        center_lat=46.0646,
        center_lon=-118.3430,
        radius_km=200.0,
    )

    assert len(points) == 1
    assert points[0].confidence == "high"
    assert points[0].brightness == 330.2
    assert points[0].acquired_at == datetime(2026, 7, 27, 19, 45, tzinfo=UTC)


def test_parse_airnow_row_normalizes_expected_fields() -> None:
    row = {
        "Latitude": "46.0668",
        "Longitude": "-118.3398",
        "AQI": 57,
        "Category": {"Name": "Moderate"},
        "ParameterName": "O3",
        "ReportingArea": "Walla Walla",
        "StateCode": "WA",
        "DateObserved": "2026-07-27",
        "HourObserved": 11,
    }

    observation = _parse_airnow_row(row, center_lat=46.0646, center_lon=-118.3430)
    assert observation is not None
    assert observation.aqi == 57
    assert observation.category == "Moderate"
    assert observation.pollutant == "O3"
    assert observation.reporting_area == "Walla Walla"


def test_parse_station_observation_temperature() -> None:
    payload = {
        "properties": {
            "timestamp": "2026-07-27T18:00:00+00:00",
            "temperature": {"value": 20.0, "unitCode": "wmoUnit:degC"},
        }
    }

    point = _parse_station_observation(
        payload,
        metric="temperature",
        station_id="KLGS",
        station_name="Walla Walla",
        latitude=46.1,
        longitude=-118.3,
    )
    assert point is not None
    assert point.value == 68.0
    assert point.unit == "°F"


def test_parse_station_observation_wind() -> None:
    payload = {
        "properties": {
            "timestamp": "2026-07-27T18:00:00+00:00",
            "windSpeed": {"value": 5.0, "unitCode": "wmoUnit:m_s-1"},
            "windDirection": {"value": 225.0, "unitCode": "wmoUnit:degree_(angle)"},
        }
    }

    point = _parse_station_observation(
        payload,
        metric="wind",
        station_id="KLGS",
        station_name="Walla Walla",
        latitude=46.1,
        longitude=-118.3,
    )
    assert point is not None
    assert point.value == 11.2
    assert point.unit == "mph"
    assert point.wind_direction == "SW"


class _NoopHttpClient:
    pass
