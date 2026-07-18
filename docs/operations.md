# Operations

## Required environment values

- `WEATHER_LOCATION_NAME`
- `WEATHER_LATITUDE`
- `WEATHER_LONGITUDE`
- `WEATHER_TIMEZONE`
- `NWS_USER_AGENT` (must include deployer contact)
- `CACHE_TTL_SECONDS`
- `STALE_DATA_MAX_SECONDS`

## Local development

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Backend:

```bash
cd backend
pip install -e ".[dev]"
uvicorn weather_api.main:app --reload --host 0.0.0.0 --port 8000
```

## Helm deployment (local chart)

```bash
helm upgrade --install weatherapp ./deploy/chart/weatherapp \
  --namespace weather \
  --create-namespace \
  --set api.image.tag=<sha-tag> \
  --set web.image.tag=<sha-tag>
```

## Basic verification

```bash
kubectl -n weather get pods,svc,ingress
kubectl -n weather rollout status deploy/weatherapp-weatherapp-api
kubectl -n weather rollout status deploy/weatherapp-weatherapp-web
curl http://weather.home.arpa/api/v1/weather
curl http://weather.home.arpa/
```

## Rollback

```bash
helm rollback weatherapp <revision> -n weather
```

## OCI chart release process

Chart releases are published by CI to GHCR as OCI artifacts:

- Chart path: `deploy/chart/weatherapp`
- Chart name: `weatherapp`
- OCI target: `oci://ghcr.io/dylanwhitetech/charts`
- Release workflow: `.github/workflows/release-chart.yml`

Release behavior:

1. Triggered by a semver git tag (`vX.Y.Z`) or manual dispatch with `chart_version`.
2. Builds and pushes both images:
   - `ghcr.io/dylanwhitetech/weatherapp-api:<source_sha>`
   - `ghcr.io/dylanwhitetech/weatherapp-web:<source_sha>`
3. Packages chart with immutable chart version `X.Y.Z`.
4. Writes production image refs into the packaged chart values using the same `<source_sha>`.
5. Pushes chart package to `oci://ghcr.io/dylanwhitetech/charts`.

### Chart values contract expected by k3s-infrastructure

Infra overrides only this contract:

- `namespace.name`
- `namespace.create`
- `ingress.enabled`
- `ingress.className`
- `ingress.host`
- `ingress.annotations`
- `serviceMonitor.enabled` (optional)
- `serviceMonitor.interval` (optional)

Infra does **not** override `api.image.*` or `web.image.*`; those are embedded by the chart release pipeline.

## Release handoff to k3s-infrastructure

After a successful chart release:

1. Send infra the exact published chart version (for example `0.2.0`).
2. Infra promotes by bumping:
   - `kubernetes/apps/weatherapp/helmrelease.yaml`
   - `spec.chart.spec.version: "<released-version>"`
3. Infra reconciles Flux and validates workload rollout.

## GHCR access note

If the GHCR chart package is private, Flux must use authentication (`secretRef`) in the infra `HelmRepository`. If package visibility is public, that extra auth wiring is not required.

## k3s-infrastructure handoff packet

When opening a dedicated session/chat in `k3s-infrastructure`, pass:

- OCI chart registry + chart name + exact released chart version
- Image repositories and immutable refs carried by that chart release
- Desired hostname and namespace
- Required Flux resources and target file paths under `kubernetes/apps`
- Reconcile and rollback commands
