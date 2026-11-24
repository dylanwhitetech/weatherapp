# Guidance index

This directory stores durable engineering decisions that should outlive a
single pull request. Keep one decision per file and link implementation/runbook
docs instead of copying procedures.

Check this index, and the records that match your topic or paths, before
starting a new scope of work.

## When to create or update a guidance record

- A change introduces, replaces, or retires a lasting behavior or constraint
  (architecture, stack, deployment, constraints).
- Future contributors need rationale to avoid re-litigating the same trade-off.
- The decision affects more than one file, workflow, or operator runbook.

Ship the record in the same PR as the change. Supersede a record rather than
deleting it.

Do not create a record for routine edits, refactors, or one-off bug fixes unless
they change a lasting decision.

## Record format

Name records `NNNN-<kebab-title>.md` and use this structure:

```markdown
# <id>: <title>

## Status
Accepted | Proposed | Superseded by <id> | Deprecated

## Context
What problem or constraint required a decision?

## Decision
What did we choose?

## Consequences
- Positive and negative follow-on effects.

## References
- Repo docs, manifests, PRs, issues, and upstream docs that justify this record.
```

## Decision map

| Decision | Topics | Affected paths |
| --- | --- | --- |
| [0001-nws-access-through-backend-service-layer.md](0001-nws-access-through-backend-service-layer.md) | NWS integration, API layering, unit conversions | `backend/src/weather_api/clients/**`, `backend/src/weather_api/services/**`, `backend/src/weather_api/main.py` |
| [0002-release-through-release-please-and-infra-promotion.md](0002-release-through-release-please-and-infra-promotion.md) | Releases, image tags, chart publishing, production promotion, rollback | `.github/workflows/release*.yml`, `deploy/chart/weatherapp/**`, `docs/operations.md` |
| [0003-structured-logging-with-loguru.md](0003-structured-logging-with-loguru.md) | Backend logging, observability | `backend/src/weather_api/telemetry/**` |
| [0004-agentic-baseline.md](0004-agentic-baseline.md) | Copilot agents, skills, field notes, code review | `AGENTS.md`, `.github/agents/**`, `.github/skills/**`, `.github/copilot-instructions.md` |
