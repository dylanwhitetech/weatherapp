# Architecture

Weatherapp runs as two containers deployed by the Helm chart in `deploy/chart/weatherapp`:

1. `weather-api` (FastAPI)
2. `weather-web` (React static site served by nginx)

## Production topology

Production is available at <https://weatherapp.dylanlabs.dev>. The public path is:

```text
Browser -> Cloudflare Tunnel (in-cluster cloudflared) -> ingress-nginx -> weatherapp web/API services
```

The cluster is managed in `dylanwhitetech/k3s-infrastructure`: three Raspberry Pi arm64 nodes running k3s v1.36.2+k3s1. Infrastructure details, disaster recovery, Cloudflare Tunnel configuration, SOPS secrets, and the Weatherapp release runbook live there:

- [Disaster recovery](https://github.com/dylanwhitetech/k3s-infrastructure/blob/main/docs/00-disaster-recovery.md)
- [Weatherapp release runbook](https://github.com/dylanwhitetech/k3s-infrastructure/blob/main/docs/03-weatherapp-release-runbook.md)
- [Cloudflare Tunnel](https://github.com/dylanwhitetech/k3s-infrastructure/blob/main/docs/05-cloudflare-tunnel.md)
- [SOPS secrets](https://github.com/dylanwhitetech/k3s-infrastructure/blob/main/docs/06-secrets-sops.md)

The old private LAN exposure model (`weather.home.arpa`, `*.home.arpa`, Pi-hole DNS, private homelab CA wildcard certs, and a Windows desktop cloudflared service) is no longer current.

## Request flow

- Browser requests `/` and static assets from `weather-web`.
- Browser requests `/api/*` from `weather-api` through ingress path routing.
- Browser-side map basemap tiles are requested from OpenStreetMap.
- `weather-api` fetches and normalizes data from NWS and map data providers.
- Prometheus scrapes `weather-api` at `/metrics` inside the cluster.

## Backend responsibilities

- NWS point discovery for the configured latitude/longitude
- Current observation, hourly forecast, daily forecast, and active alert retrieval
- Background cache refresh on startup and every `CACHE_TTL_SECONDS`
- In-memory cache with TTL + stale fallback up to `STALE_DATA_MAX_SECONDS`
- Golf and lawn recommendation generation
- Map panel configuration and overlays for precipitation, fires, air quality, temperature, and wind
- Health and metrics endpoints
- NDJSON structured logging through loguru

## Frontend responsibilities

- Fetch and render dashboard payload from `/api/v1/weather`
- Expose stale-data warning states
- Present map, current, hourly, daily, alert, golf, and lawn sections
- Refresh every 10 minutes plus manual refresh
- Proxy `/api`, `/health`, and `/metrics` to the backend during local Vite development

## Release and deployment model

Application releases are automated by release-please and Flux promotion. See [operations.md](operations.md#how-to-ship-a-change) rather than duplicating the release sequence here.
