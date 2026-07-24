# Contributing to weatherapp

Thanks for contributing. This repo accepts application code, deployment changes,
documentation updates, and Copilot customizations, but all contributions should
stay aligned with the repo's runtime model and AI standards.

## Start here

1. Read `AGENTS.md`.
2. Read `.github/copilot-instructions.md`.
3. If you are adding a new agent or skill, inspect
   `https://github.com/github/awesome-copilot` first for prior art.

For a copy-ready standards block you can reuse in other repos, use
`AGENTS.md` section **Shared standards (portable baseline)**.

## Code standards (single source of truth)

All code standards live in `AGENTS.md`:

- `Shared standards (portable baseline)`
- `Weatherapp engineering rules`

This keeps standards in one human-readable location and makes cross-repo reuse
easier. Update standards in `AGENTS.md` first, then adjust links elsewhere.

## AI customization standards

### Reference baseline

Before adding a new agent or skill, check these first:

- `https://awesome-copilot.github.com/agents`
- `https://awesome-copilot.github.com/skills`
- `https://awesome-copilot.github.com/llms.txt`
- `https://github.com/github/awesome-copilot`

Prefer adapting an existing example over writing a new structure from scratch.
If you still need a new artifact, keep the same shape and naming conventions.

### Where to place AI artifacts

| Artifact | Location |
| --- | --- |
| Repo-wide Copilot defaults | `.github/copilot-instructions.md` |
| Runtime skills for this repo | `.github/skills/<skill>/SKILL.md` |
| Custom agents | `agents/<name>.agent.md` |
| CLI extensions | `.github/extensions/<extension-id>/` |

### Agent requirements

- Lowercase-hyphen file name with `.agent.md`
- Frontmatter with `name` and `description`
- Clear scope, expertise, and constraints
- Prefer professional, direct review behavior over gimmick personas
- Note the upstream `awesome-copilot` example used as inspiration in the PR

### Skill requirements

- Lowercase-hyphen folder name
- `SKILL.md` with `name` and `description`
- Explicit trigger conditions
- Repeatable phase/checklist workflow
- Output contract that says what "done" looks like
- Bundled assets referenced from the skill when applicable

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
  impact.
- If you added or changed an agent/skill, name the `awesome-copilot` reference
  you started from.

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

If you changed the Helm chart and Helm is available locally, run:

```bash
helm lint deploy/chart/weatherapp
```

## Documentation expectations

Update docs when you change:

- API behavior
- local development flow
- deployment or release behavior
- AI standards, agents, skills, templates, or extension workflows
