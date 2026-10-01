# Incident Troubleshooting Runbook

This runbook covers the most common failure modes for the weatherapp backend and how to diagnose them using logs and Prometheus metrics.

## Log access

### Local (Docker Compose)

```bash
docker compose logs -f api
```

Logs are NDJSON (one JSON object per line). Filter with `jq`:

```bash
docker compose logs api | jq 'select(.record.level.name == "ERROR")'
```

### k3s (production)

```bash
kubectl -n weather logs -f deploy/weatherapp-weatherapp-api
```

With `jq` filtering:

```bash
kubectl -n weather logs deploy/weatherapp-weatherapp-api | jq 'select(.record.level.name == "WARNING" or .record.level.name == "ERROR")'
```

### Loki / Grafana (if configured)

Query all error-level events from the last hour:

```logql
{namespace="weather", app="weatherapp-api"} | json | level = "ERROR"
```

Query NWS upstream failures:

```logql
{namespace="weather", app="weatherapp-api"} | json | message = "NWS request failed"
```

---

## Log field reference

Every log line emitted by the backend is a JSON object. Key fields:

| Field | Description |
| --- | --- |
| `text` | Rendered log line |
| `record.message` | The log message string |
| `record.level.name` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `record.time.timestamp` | Unix timestamp |
| `record.extra.*` | Contextual key-value pairs (see below) |

Common contextual fields:

| Field | Where emitted | Description |
| --- | --- | --- |
| `endpoint` | NWS client | NWS endpoint name (`forecast`, `hourly`, `observation`, etc.) |
| `url` | NWS client (`DEBUG` only) | Full NWS URL |
| `attempt` | NWS client | Retry attempt number |
| `error_type` | NWS client, cache | Exception class name |
| `duration_ms` | NWS client | Request duration in milliseconds |
| `cache_age_seconds` | Cache | Age of the cached payload |
| `location` | Weather service | Configured location name |
| `hourly_periods` | Weather service | Count of hourly forecast periods returned |
| `alerts` | Weather service | Count of active alerts |
| `log_level` | Startup | Effective log level |

---

## Common incidents

### 1. Dashboard shows no data (`503 weather_unavailable`)

**Symptoms:**

- `/api/v1/weather` returns `503` with `"code": "weather_unavailable"`
- `/health/ready` returns `503` with `"status": "not_ready"`

**Diagnosis:**

```bash
kubectl -n weather logs deploy/weatherapp-weatherapp-api | jq 'select(.record.message | test("unavailable|NWS request failed"))'
```

Look for:

- `"Weather data unavailable"` — no usable data in cache and upstream is also failing
- `"NWS request failed"` — NWS API is unreachable or returning errors
- `error_type` field on the error log (for example `ConnectError`, `HTTPStatusError`)

**Resolution:**

1. Verify NWS API is reachable: `curl -s https://api.weather.gov/points/<lat>,<lon>` (replace with your coords).
2. Check `NWS_USER_AGENT` is set and includes a valid contact address — NWS blocks requests with missing or generic user agents.
3. If NWS is having an outage, monitor [status.weather.gov](https://status.weather.gov). The service will recover automatically once NWS returns successful responses.

---

### 2. Dashboard shows stale data

**Symptoms:**

- Response payload has `"metadata.stale": true`
- `weather_data_stale` Prometheus gauge is `1`
- Frontend shows a stale-data warning banner

**Diagnosis:**

```bash
kubectl -n weather logs deploy/weatherapp-weatherapp-api | jq 'select(.record.message == "Serving stale weather data")'
```

The `cache_age_seconds` field shows how old the data is. Compare against `CACHE_TTL_SECONDS` (fresh threshold) and `STALE_DATA_MAX_SECONDS` (hard limit).

**Resolution:**

- Stale data is expected during brief NWS outages. The service recovers automatically.
- If `cache_age_seconds` is approaching `STALE_DATA_MAX_SECONDS`, NWS is likely experiencing a sustained outage. See incident #1 for investigation steps.
- If NWS is healthy but refreshes are failing, check `NWS request failed` logs for a persistent `error_type`.

---

### 3. NWS request retries / intermittent failures

**Symptoms:**

- `weather_upstream_errors_total` Prometheus counter is incrementing
- `WARNING` log lines with `"NWS request error, retrying"`

**Diagnosis:**

```bash
kubectl -n weather logs deploy/weatherapp-weatherapp-api | jq 'select(.record.message == "NWS request error, retrying")'
```

Check `error_type` and `endpoint` fields to identify which NWS endpoint is failing.

**Resolution:**

- Transient retries (`attempt: 1`) are normal. Up to `NWS_MAX_RETRIES` retries are attempted with exponential backoff.
- Sustained retries on a single endpoint usually indicate a NWS outage for that zone or data type. Monitor and wait.
- If `error_type` is `TimeoutException`, consider increasing `NWS_TIMEOUT_SECONDS`.

---

### 4. Pod crash loop / container restart

**Symptoms:**

- `kubectl -n weather get pods` shows `CrashLoopBackOff` or high restart count

**Diagnosis:**

```bash
kubectl -n weather logs deploy/weatherapp-weatherapp-api --previous
```

Look for:

- Missing or malformed environment variables at startup
- Port binding errors

**Resolution:**

1. Verify all required environment variables are set in the Helm values / k3s configuration. See [Required and optional environment values](operations.md#required-and-optional-environment-values).
2. Check liveness probe in-cluster: `kubectl -n weather port-forward svc/weatherapp-weatherapp-api 8000:8000`, then `curl http://localhost:8000/health/live`.
3. If the container exits without log output, check the Dockerfile `CMD` and ensure `uvicorn` is starting correctly.

---

### 5. No data on fresh deployment (`/health/ready` → 503)

**Symptoms:**

- Pod is running but `/health/ready` returns `503`
- Log shows `"weather-api starting"` followed by repeated `"background weather refresh failed"`

**Explanation:**

On startup, a background refresh loop populates the cache without waiting for inbound traffic. Readiness stays `503` until the first refresh succeeds, then Kubernetes can route traffic to the pod.

**Diagnosis:**

```bash
kubectl -n weather logs deploy/weatherapp-weatherapp-api | jq 'select(.record.message | test("starting|refreshed|background weather refresh failed|failed"))'
```

If `"Weather cache refreshed successfully"` never appears, the initial fetch is failing. Follow incident #1 for NWS connectivity investigation.

---

### 6. Map layer unavailable or empty

**Symptoms:**

- A layer tab is disabled or shows an unavailable message
- Map overlay requests return a `map_layer_error`

**Diagnosis:**

```bash
kubectl -n weather logs deploy/weatherapp-weatherapp-api | jq 'select(.record.message | test("map|AirNow|FIRMS|RainViewer|observation"; "i"))'
```

Check whether the layer requires optional configuration. Air quality requires `AIRNOW_API_KEY`; precipitation uses `RAINVIEWER_API_URL`; fire detections use the FIRMS CSV URLs; observation layers use NWS station data.

**Resolution:**

- Configure missing optional provider settings through the deployment values or secret process.
- For provider outages, leave the layer unavailable and retry after the provider recovers.
- Do not put provider keys in frontend code or logs.

---

## Prometheus metric cross-reference

| Metric | Alert signal |
| --- | --- |
| `weather_data_stale` | `1` — serving stale data |
| `weather_last_successful_refresh_timestamp_seconds` | Very old — sustained upstream failure |
| `weather_upstream_errors_total` | Incrementing fast — NWS errors |
| `weather_cache_misses_total` | Incrementing without matching refresh — cache thrash |
| `weather_api_requests_total{status="503"}` | Incrementing — clients receiving errors |

---

## Future enhancements

- **Request correlation IDs**: Add a FastAPI middleware to generate and bind a `request_id` to each log context, enabling end-to-end log tracing per request.
- **Loki alerting rules**: Add `ruler` rules in Grafana for `level = "ERROR"` log volume thresholds.
