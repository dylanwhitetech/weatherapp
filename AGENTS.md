# AGENTS.md

Rules for agents and contributors that cannot be worked out from the code,
README, or docs. Keep this file short; do not add repo overviews.

## Agents and loops

| Agent | Use |
| --- | --- |
| `weatherapp-main` | Intended entry agent, selected by the user for each session. Plans, implements, and delegates. |
| `weatherapp-test` | Writes and runs tests. Background subagent or its own worktree session. |
| `weatherapp-deploy` | Release-please release, SHA-tagged images, infra promotion PR, rollout check. |

- Select `weatherapp-main` at the start of each session (see
  `CONTRIBUTING.md`, "Copilot agents"). No repo file enforces this.
- Delegation is one hop: subagents cannot create subagents, so give them
  complete context.
- Pull requests use built-in Copilot code review on GitHub; there is no custom
  review agent.
- **Guidance**: before new scope, check `guidance/README.md` and matching
  records. When a change introduces, replaces, or retires a lasting decision
  (architecture, stack, deployment, constraints), add or update a record in the
  same PR. Supersede rather than delete.
- **Field notes**: use the `field-notes` skill when an agent or skill was wrong
  or blocked and a fix was found, a command was retried with changes, the user
  corrected the agent, or guidance was missing or stale. Notes go in the
  session files folder, never the repo.
- **Authoring**: use the `copilot-authoring` skill before adding or editing
  agents, skills, or instructions. Create a new skill only when a field note or
  failure shows the need. Check `github/awesome-copilot` first and cite the
  example used in the PR.
- **Resources**: when the user shares a new agentic resource, append it to
  `.github/skills/copilot-authoring/references.md`.

## Communication

Lead with the conclusion or requested action, then supporting points, then
evidence ([Minto Pyramid](https://untools.co/minto-pyramid/)). State
uncertainty, blockers, and tradeoffs plainly.

## Backend

- All async code uses `asyncio`.
- NWS access stays in the backend service layer; route handlers never call NWS
  directly (`guidance/0001-nws-access-through-backend-service-layer.md`).
- Reuse `_mps_to_mph`, `_c_to_f`, `_wind_direction`, and `_parse_wind_values`
  when those conversions apply.

### Logging

- Use loguru (`from loguru import logger`). `configure_logging(settings.log_level)`
  runs once at startup and emits NDJSON to stdout.
- Pass context as keyword arguments (`logger.info("msg", key=value)`) or with
  `logger.bind(...)`.
- `logger.warning` for recoverable degraded states (stale data, retries);
  `logger.error` for unrecoverable failures.
- Never log credentials, tokens, or personal data.

## Frontend

- Preserve proxy-based local API behavior unless the change intentionally
  updates the local development contract.
- Keep UI state transitions, stale-data warnings, and refresh behavior
  coherent.

## Secrets, docs, and release

- Never put secrets, passwords, tokens, or real credentials in source, prompts,
  examples, templates, or logs. Use placeholders such as `ask admin`.
- Behavior changes include the smallest relevant tests and update user- or
  operator-facing docs when the contract changes.
- Normal releases follow `docs/operations.md`: release-please, SHA image tags,
  and promotion through `dylanwhitetech/k3s-infrastructure`. Never manually
  bump versions. Manually tag or dispatch `release-chart` only as documented
  fallbacks when release automation is broken. Never mutate the cluster
  directly.

## Pull requests

- GitHub Flow: short-lived branches, PRs into `main`, one concern per PR.
- Conventional Commit PR titles (they drive release-please).
- A human review is required before merge.
