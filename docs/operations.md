# Operations

## Required and optional environment values

The backend reads these settings from environment variables or `.env`.

Required for an accurate deployment:

- `WEATHER_LOCATION_NAME`
- `WEATHER_LATITUDE`
- `WEATHER_LONGITUDE`
- `WEATHER_TIMEZONE`
- `NWS_USER_AGENT` (must include deployer contact)
- `CACHE_TTL_SECONDS`
- `STALE_DATA_MAX_SECONDS`

Optional runtime and provider settings:

- `LOG_LEVEL` (default `INFO`; use `DEBUG` for per-request NWS URL tracing)
- `NWS_BASE_URL`
- `NWS_TIMEOUT_SECONDS`
- `NWS_MAX_RETRIES`
- `NWS_BACKOFF_SECONDS`
- `MAP_TIMEOUT_SECONDS`
- `MAP_CYCLE_SECONDS`
- `MAP_DEFAULT_ZOOM`
- `MAP_OVERLAY_OPACITY`
- `MAP_CACHE_TTL_SECONDS`
- `MAP_OBSERVATION_STATION_LIMIT`
- `MAP_OBSERVATION_POINT_LIMIT`
- `AIRNOW_API_KEY` (required for the air-quality map layer)
- `AIRNOW_BASE_URL`
- `AIRNOW_SEARCH_DISTANCE_MILES`
- `AIRNOW_MAX_OBSERVATIONS`
- `RAINVIEWER_API_URL`
- `FIRMS_VIIRS_SNPP_CSV_URL`
- `FIRMS_VIIRS_NOAA20_CSV_URL`
- `FIRMS_SEARCH_RADIUS_KM`
- `FIRMS_MAX_POINTS`

`OPENWEATHER_API_KEY` is deprecated in code and retained only so older `.env` files do not break startup.

## Local development

Frontend:

```bash
cd frontend
npm ci
npm run dev
```

Backend through Docker Compose:

```bash
make local-up
make local-logs
make local-down
```

Backend without Docker:

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

## Deployed access

The deployed Weatherapp is available at <https://weatherapp.dylanlabs.dev>.
The public hostname is served by the k3s cluster through an in-cluster Cloudflare Tunnel, ingress-nginx, and the weatherapp chart. The chart default `ingress.host` is `weatherapp.dylanlabs.dev`.

Cluster, DNS, tunnel, secrets, and disaster-recovery details are owned by [`dylanwhitetech/k3s-infrastructure`](https://github.com/dylanwhitetech/k3s-infrastructure). See its docs instead of duplicating operational detail here:

- [Disaster recovery](https://github.com/dylanwhitetech/k3s-infrastructure/blob/main/docs/00-disaster-recovery.md)
- [Weatherapp release runbook](https://github.com/dylanwhitetech/k3s-infrastructure/blob/main/docs/03-weatherapp-release-runbook.md)
- [Cloudflare Tunnel](https://github.com/dylanwhitetech/k3s-infrastructure/blob/main/docs/05-cloudflare-tunnel.md)
- [SOPS secrets](https://github.com/dylanwhitetech/k3s-infrastructure/blob/main/docs/06-secrets-sops.md)

Removed operating models that should not be used for new work: Pi-hole DNS, `weather.home.arpa`, `*.home.arpa`, private homelab CA wildcard certificates, a Windows desktop cloudflared service, GHCR chart pull secrets for public packages, and `:latest` image tags.

## Basic verification

```bash
kubectl -n weather get pods,svc,ingress
kubectl -n weather rollout status deploy/weatherapp-weatherapp-api
kubectl -n weather rollout status deploy/weatherapp-weatherapp-web
curl https://weatherapp.dylanlabs.dev/api/v1/weather
curl https://weatherapp.dylanlabs.dev/
```

Health endpoints (`/health/live`, `/health/ready`) are not routed to the API through the public Ingress, which only sends `/api` to the API. Check them in-cluster:

```bash
kubectl -n weather port-forward svc/weatherapp-weatherapp-api 8000:8000
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

## Rollback

For an intentional production rollback, revert the `dylanwhitetech/k3s-infrastructure` promotion PR that bumped `kubernetes/apps/weatherapp/helmrelease.yaml` `spec.chart.spec.version`. Flux then returns the HelmRelease to the previous chart version.

The infra HelmRelease is configured with upgrade remediation (`retries: 1`, `strategy: rollback`, `remediateLastFailure: true`), so a failed upgrade should automatically roll back and leave the HelmRelease reporting the failure for follow-up.

## Incident troubleshooting

See [runbook.md](runbook.md) for step-by-step diagnosis of common failures (NWS outages, stale data, crash loops, no data on startup) and Prometheus metric cross-references.

## OCI chart release process

Current release-please version: `0.1.4`.

### How to ship a change

1. Merge your PR to `main`. Every PR must pass `test.yml`, which includes backend Ruff + pytest, frontend lint + Vitest + build, Helm lint, and `chart-smoke`. The smoke job installs the chart into a throwaway kind cluster with images built from that commit and curls `/health/live`, `/health/ready`, `/api/v1/weather`, and the web root. Use a Conventional Commit PR title: `fix:` cuts a patch release, `feat:` cuts a minor release (`bump-minor-pre-major` means this is a patch while pre-1.0), and `feat!:` cuts a breaking release. `docs:`, `ci:`, `chore:`, `test:`, and `refactor:` do not cut a release.
2. `release.yml` (release-please) opens or updates a PR named `chore(main): release X.Y.Z` with the version bump and `CHANGELOG.md`. Let releasable changes accumulate there; nothing ships until it is merged.
3. Merge the release PR. release-please tags `vX.Y.Z`, creates the GitHub Release, and calls `release-chart.yml`, which builds SHA-tagged multi-arch images, publishes chart `X.Y.Z` to `oci://ghcr.io/dylanwhitetech/charts`, and opens an infra PR, `chore(weatherapp): promote weatherapp chart X.Y.Z`.
4. The owner merges that infra PR. Flux deploys it. If the new release fails readiness, Flux rolls back automatically and the HelmRelease stays `Ready=False` with the error until a fixed version is promoted.
5. Rollback on purpose: revert the infra promotion PR.

No manual tagging or version bumps. release-please owns `.release-please-manifest.json` and `deploy/chart/weatherapp/Chart.yaml`; images are tagged only with the commit SHA (no `:latest`). Fallbacks if automation is broken: manually push a `vX.Y.Z` tag or run `release-chart` with workflow dispatch using `chart_version` and `source_sha`.

One-time repo setting required by release-please: **Settings → Actions → General → Allow GitHub Actions to create and approve pull requests**.

### Pipeline details

Chart releases are published by CI to GHCR as public OCI artifacts:

- Chart path: `deploy/chart/weatherapp`
- Chart name: `weatherapp`
- OCI target: `oci://ghcr.io/dylanwhitetech/charts`
- Release workflow: `.github/workflows/release-chart.yml`

Release behavior:

1. Called by `release.yml` when a release PR merges. It also supports a manually pushed `vX.Y.Z` tag and manual dispatch with `chart_version`.
2. Builds and pushes both images:
   - `ghcr.io/dylanwhitetech/weatherapp-api:<source_sha>`
   - `ghcr.io/dylanwhitetech/weatherapp-web:<source_sha>`
3. Packages chart with immutable chart version `X.Y.Z`.
4. Writes production image refs into the packaged chart values using the same `<source_sha>`.
5. Pushes chart package to `oci://ghcr.io/dylanwhitetech/charts`.
6. Opens or updates the infra promotion PR when `K3S_INFRA_REPO` and `K3S_INFRA_REPO_TOKEN` are configured.

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

After a successful chart release, this repo can automatically open/update an infra PR that bumps `spec.chart.spec.version`.

### Enabling automated infra PR creation

Configure these in the `weatherapp` repository:

- Repository variable: `K3S_INFRA_REPO` (for example `dylanwhitetech/k3s-infrastructure`)
- Secret: `K3S_INFRA_REPO_TOKEN` (PAT with write access to the infra repo contents + pull requests)
- Optional repository variable: `K3S_INFRA_BASE_BRANCH` (default: `main`)
- Optional repository variable: `K3S_INFRA_HELMRELEASE_PATH` (default: `kubernetes/apps/weatherapp/helmrelease.yaml`)

When configured, `.github/workflows/release-chart.yml` creates or updates an infra PR on branch `automation/weatherapp-chart-<version>`.

### Manual fallback

If auto PR wiring is not configured, promote manually after release:

1. Update `kubernetes/apps/weatherapp/helmrelease.yaml` in `dylanwhitetech/k3s-infrastructure`.
2. Set `spec.chart.spec.version: "<released-version>"`.
3. Open and merge the infra PR, then reconcile Flux and validate rollout.

## GHCR access note

The Weatherapp GHCR image and chart packages are public. Do not configure `ghcr-weatherapp-charts-auth` or other chart pull secrets for the current production path.

## k3s-infrastructure handoff packet

When opening a dedicated session/chat in `k3s-infrastructure`, pass:

- OCI chart registry + chart name + exact released chart version
- Image repositories and immutable refs carried by that chart release
- Desired hostname and namespace
- Required Flux resources and target file paths under `kubernetes/apps`
- Reconcile and rollback commands
