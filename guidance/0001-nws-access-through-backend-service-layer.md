# 0001: Keep NWS access in the backend service layer

## Status
Accepted

## Context
The dashboard depends on the National Weather Service API, which requires an
identifying `NWS_USER_AGENT`, can be slow or unavailable, and returns units and
shapes that need normalizing. Spreading upstream calls across route handlers
would duplicate retries, caching, stale-data handling, and unit conversion.

## Decision
Only the backend talks to NWS, through `weather_api.clients.nws` and the
services in `weather_api.services`. FastAPI route handlers in
`weather_api.main` call services and never call NWS directly. Unit and wind
parsing reuse the existing helpers (`_mps_to_mph`, `_c_to_f`,
`_wind_direction`, `_parse_wind_values`).

## Consequences
- Retries, backoff, caching, and stale-data fallbacks live in one place.
- The frontend only consumes the normalized `/api/v1/*` contract.
- New providers or endpoints must be added behind a service, not in routes.

## References
- [AGENTS.md](../AGENTS.md) (backend rules)
- [docs/architecture.md](../docs/architecture.md)
- [docs/runbook.md](../docs/runbook.md) (NWS outage and stale-data diagnosis)
- [NWS API documentation](https://www.weather.gov/documentation/services-web-api)
