# Contributing to weatherapp

Thanks for contributing. This repo accepts application code, deployment changes,
documentation updates, and Copilot customizations, but all contributions should
stay aligned with the repo's runtime model and AI standards.

## Start here

1. Read `AGENTS.md` (canonical repo rules).
2. Check `guidance/README.md` and any records that match your change.
3. Before adding or editing an agent, skill, or instruction file, follow
   `.github/skills/copilot-authoring/SKILL.md`.

## Code standards

Repo-specific rules live in `AGENTS.md`. General expectations:

- Use meaningful names, keep functions single-purpose, and handle errors
  explicitly.
- Prefer simple, maintainable code over premature optimization or speculative
  features; avoid duplication and comments that add no value.
- Keep dependencies current.
- Relevant tests must pass and at least one human must review before merge.

## Copilot agents

| Agent | Purpose |
| --- | --- |
| `weatherapp-main` | Intended entry agent, selected by the user: plans, implements, delegates |
| `weatherapp-test` | Writes and runs tests |
| `weatherapp-deploy` | Release, infra promotion PR, rollout verification |

Agents live in `.github/agents/`. No repository file can make an agent the
automatic default, so select `weatherapp-main` when you start a session:

- **GitHub Copilot app**: choose `weatherapp-main` from the agent picker in the
  prompt box, or type `/agent`. To nudge every session, you can also add "Use
  the weatherapp-main agent" to the repository's Instructions field (Settings →
  Repositories → weatherapp); this is guidance, not enforcement.
- **Copilot CLI**: run `copilot --agent=weatherapp-main`, or type `/agent`
  in an interactive session.
- **Copilot cloud agent on GitHub.com**: on the Agents tab, pick
  `weatherapp-main` from the agent dropdown in the prompt box. Repository
  agents appear there only after they are merged to the default branch.

Code review uses built-in Copilot code review on GitHub; there is no custom
review agent.

## AI customization standards

| Artifact | Location |
| --- | --- |
| Canonical rules | `AGENTS.md` |
| Copilot pointer | `.github/copilot-instructions.md` |
| Custom agents | `.github/agents/<name>.agent.md` |
| Skills | `.github/skills/<skill>/SKILL.md` |
| CLI extensions | `.github/extensions/<extension-id>/` |
| Durable decisions | `guidance/NNNN-<title>.md` |

- Formats, frontmatter, and writing rules: `.github/skills/copilot-authoring/SKILL.md`.
- Resource catalogue: `.github/skills/copilot-authoring/references.md`.
- Add a skill only when a field note or observed failure shows the need.
- Check `github/awesome-copilot` for prior art and name the example you
  started from in the PR.
## Commit, branch, PR, and issue standards

### Branches

- Branch from `main`.
- Keep branches short-lived and task-focused.
- Use descriptive kebab-case names.

### Commits

Use Conventional Commits:

```text
<type>[optional scope]: <description>
```

Examples:

- `feat(frontend): add stale data banner`
- `fix(api): guard missing dewpoint conversion`
- `docs(ai): add agent authoring standards`

### Pull requests

- Open PRs against `main`.
- Use the PR template.
- Link the issue.
- Describe user impact, validation performed, and any chart or operational
  impact. Release behavior is documented in `docs/operations.md`; do not manually tag or bump release versions during normal shipping.
- If you added or changed an agent/skill, name the `awesome-copilot` reference
  you started from.
- Update `guidance/` in the same PR when the change alters a lasting decision.

### Issues

Use the issue forms whenever possible. A good issue should include:

- the problem or opportunity
- current vs expected behavior
- impact and affected surface
- acceptance criteria
- links to references or prior art

For AI infra or customization issues, include whether the request affects
instructions, skills, agents, templates, extensions, or workflow automation.

## Validation

Run the smallest relevant checks for the files you touched:

```bash
make backend-test
make frontend-test
cd frontend && npm run build
cd frontend && npm run lint
```

If backend Python tooling is installed, also run:

```bash
cd backend && python -m ruff check src tests
```

CI also runs Helm lint and the `chart-smoke` kind install on pull requests. If you changed the Helm chart and Helm is available locally, run:

```bash
helm lint deploy/chart/weatherapp
```

## Documentation expectations

Update docs when you change:

- API behavior
- local development flow
- deployment or release behavior
- AI standards, agents, skills, templates, or extension workflows
- a lasting decision recorded in `guidance/`
