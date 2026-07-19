# Architecture

The MVP uses two containers:

1. `weather-api` (FastAPI)
2. `weather-web` (React + static nginx)

Traffic flow:

- Browser requests `/` and static assets from `weather-web`
- Browser requests `/api/*` from `weather-api` through ingress path routing
- `weather-api` fetches and normalizes data from `api.weather.gov`
- Prometheus scrapes `weather-api` at `/metrics`

## Backend responsibilities

- NWS point discovery for configured latitude/longitude
- Current observation, hourly forecast, daily forecast, and active alert retrieval
- In-memory cache with TTL + stale fallback
- Golf and lawn recommendation generation
- Health and metrics endpoints

## Frontend responsibilities

- Fetch and render dashboard payload from `/api/v1/weather`
- Expose stale-data warning states
- Present current, hourly, daily, alert, golf, and lawn sections
- Refresh every 10 minutes plus manual refresh
