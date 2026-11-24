# 0003: Structured NDJSON logging with loguru

## Status
Accepted

## Context
Backend logs are collected from k3s pods by Loki and other aggregators, which
need machine-readable, consistently structured records.

## Decision
All backend logging uses loguru. `configure_logging(settings.log_level)` in
`weather_api.telemetry.logging` runs once at startup and emits NDJSON to
stdout. `LOG_LEVEL` controls verbosity (default `INFO`). Contextual fields are
passed as keyword arguments or bound with `logger.bind`.

## Consequences
- Logs are queryable by field without custom parsing.
- Standard-library `logging` calls and print statements are not used.
- Credentials, tokens, and personal data must never be logged.

## References
- [AGENTS.md](../AGENTS.md) (structured logging rules)
- [docs/runbook.md](../docs/runbook.md)
- PR #14 (structured logging with loguru)
- [loguru](https://github.com/Delgan/loguru)
