# API

Base path: `/api/v1`

## Dashboard endpoints

- `GET /api/v1/weather` - full dashboard payload, including location, current conditions, hourly and daily forecasts, alerts, recommendations, metadata, and map panel configuration
- `GET /api/v1/current` - current conditions from the dashboard payload
- `GET /api/v1/hourly?hours=24` - hourly forecast (clamped to 1..48)
- `GET /api/v1/forecast` - daily forecast
- `GET /api/v1/alerts` - active alerts
- `GET /api/v1/recommendations` - golf and lawn recommendations

## Map endpoints

The dashboard payload advertises available layers in `map_panel.layers`. The frontend uses these URLs when a layer is enabled:

- `GET /api/v1/maps/tiles/{layer_id}/{z}/{x}/{y}.png` - tile overlay for tile-backed map layers such as precipitation
- `GET /api/v1/maps/fires` - active fire detections near the configured location
- `GET /api/v1/maps/air-quality` - AirNow air-quality observations; unavailable unless `AIRNOW_API_KEY` is configured
- `GET /api/v1/maps/observations/temperature` - nearby NWS station temperature observations
- `GET /api/v1/maps/observations/wind` - nearby NWS station wind observations

Unknown map layers or observation metrics return `404` with `detail.code = "map_layer_error"`. Upstream map-provider failures return a map-layer error status with the same detail code.

## Health and metrics

- `GET /health/live` - process liveness
- `GET /health/ready` - readiness based on cached data freshness/staleness
- `GET /metrics` - Prometheus metrics

The production Ingress routes `/api` to the API service and `/` to the web service. Check `/health/*` and `/metrics` in-cluster or through a port-forward rather than through the public hostname.
