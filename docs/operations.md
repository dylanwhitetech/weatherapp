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

## Deployed access

The deployed WeatherApp is available at <https://weatherapp.dylanlabs.dev>.
The public hostname, DNS, TLS, Cloudflare Tunnel, and Kubernetes exposure are
environment-specific and owned by
[`dylanwhitetech/k3s-infrastructure`](https://github.com/dylanwhitetech/k3s-infrastructure)
(see `docs/05-cloudflare-tunnel.md`). The chart's default `ingress.host` matches
this hostname. The former private LAN path (`weather.home.arpa` via Pi-hole and a
homelab CA) is deprecated.

## Basic verification

```bash
kubectl -n weather get pods,svc,ingress
kubectl -n weather rollout status deploy/weatherapp-weatherapp-api
kubectl -n weather rollout status deploy/weatherapp-weatherapp-web
curl https://weatherapp.dylanlabs.dev/api/v1/weather
curl https://weatherapp.dylanlabs.dev/
```

Health endpoints (`/health/live`, `/health/ready`) are not routed through the
public Ingress, which only sends `/api` to the API. Check them in-cluster:

```bash
kubectl -n weather port-forward svc/weatherapp-weatherapp-api 8000:8000
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

## Rollback

```bash
helm rollback weatherapp <revision> -n weather
```

## Incident troubleshooting

See [runbook.md](runbook.md) for step-by-step diagnosis of common failures
(NWS outages, stale data, crash loops, no data on startup) and Prometheus metric
cross-references.

## OCI chart release process

### How to ship a change

1. Merge your PR to `main`. Every PR must pass `test.yml`, which includes
   `chart-smoke`: the chart is installed into a throwaway kind cluster with
   images built from that commit and must reach readiness.
   Use a Conventional Commit PR title: `fix:` cuts a patch release, `feat:` a
   minor release (patch while pre-1.0), and `feat!:` a breaking release.
   `docs:`, `ci:`, `chore:`, `test:` and `refactor:` do not cut a release.
2. `release.yml` (release-please) opens or updates a PR named
   `chore(main): release X.Y.Z` with the version bump and `CHANGELOG.md`.
   Let releasable changes accumulate there; nothing ships until it is merged.
3. Merge the release PR. release-please tags `vX.Y.Z`, creates the GitHub
   Release, and calls `release-chart.yml`, which publishes chart `X.Y.Z` with
   SHA-pinned images and opens an infra PR,
   `chore(weatherapp): promote weatherapp chart X.Y.Z`.
4. Merge that infra PR. Flux deploys it. If the new release fails readiness,
   Flux rolls back to the previous release automatically, and the HelmRelease
   stays `Ready=False` with the error until a fixed version is promoted.
5. Rollback on purpose: revert the infra promotion PR.

No manual tagging or version bumps. release-please owns the version in
`.release-please-manifest.json` and `Chart.yaml`; images are tagged only with
the commit SHA (no `:latest`). Fallback if automation is broken: run
`release-chart` manually (workflow dispatch) with `chart_version` and
`source_sha`.

One-time repo setting required by release-please: **Settings → Actions →
General → Allow GitHub Actions to create and approve pull requests**.

### Pipeline details

Chart releases are published by CI to GHCR as OCI artifacts:

- Chart path: `deploy/chart/weatherapp`
- Chart name: `weatherapp`
- OCI target: `oci://ghcr.io/dylanwhitetech/charts`
- Release workflow: `.github/workflows/release-chart.yml`

Release behavior:

1. Called by `release.yml` when a release PR merges (also runs on a manually
   pushed `vX.Y.Z` tag or manual dispatch with `chart_version`).
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

1. Update `kubernetes/apps/weatherapp/helmrelease.yaml`.
2. Set `spec.chart.spec.version: "<released-version>"`.
3. Open and merge the infra PR, then reconcile Flux and validate rollout.

## GHCR access note

If the GHCR chart package is private, Flux must use authentication (`secretRef`) in the infra `HelmRepository`. If package visibility is public, that extra auth wiring is not required.

## k3s-infrastructure handoff packet

When opening a dedicated session/chat in `k3s-infrastructure`, pass:

- OCI chart registry + chart name + exact released chart version
- Image repositories and immutable refs carried by that chart release
- Desired hostname and namespace
- Required Flux resources and target file paths under `kubernetes/apps`
- Reconcile and rollback commands
