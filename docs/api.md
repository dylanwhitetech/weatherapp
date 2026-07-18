# API

Base path: `/api/v1`

## Endpoints

- `GET /api/v1/weather` - full dashboard payload
- `GET /api/v1/current` - current conditions
- `GET /api/v1/hourly?hours=24` - hourly forecast (clamped to 1..48)
- `GET /api/v1/forecast` - daily forecast
- `GET /api/v1/alerts` - active alerts
- `GET /api/v1/recommendations` - golf and lawn recommendations

## Health and metrics

- `GET /health/live` - process liveness
- `GET /health/ready` - readiness based on cached data freshness/staleness
- `GET /metrics` - Prometheus metrics
