# AGENTS.md

## Purpose

This repository uses GitHub Copilot customizations to capture weatherapp-specific
engineering standards, review guidance, and repeatable workflows.

## Shared standards (portable baseline)

These rules apply to every file in the repository and are intentionally compact
so they can be reused in other repos.

### Must have

- Git must be used for version control and code management.
- Code must use meaningful variable and function names.
- Relevant tests must run and pass before merge.
- Code must be reviewed by at least one developer before merge.
- Documentation examples must use placeholders such as `ask admin` instead of
  real credentials or passwords.

### Should have

- Code should avoid global variables whenever practical.
- Exception handling should be used to handle errors gracefully.
- Dependencies should be updated regularly for security and compatibility.
- Single Responsibility should guide functions and classes.
- DRY (Don't Repeat Yourself) should be followed.
- KISS (Keep It Simple, Stupid) should be followed.
- YAGNI (You Aren't Gonna Need It) should be followed.
- DMMT (Don't Make Me Think) should be followed.
- KIM (Keep It Maintainable) should be followed.
- APO (Avoid Premature Optimization) should be followed.
- SOC (Separation of Concerns) should be followed.

### Could have

- Complex code could include clarifying comments, but refactoring for readability
  is preferred first.

### Won't have

- Code won't include unnecessary duplication.
- Code won't include unnecessary comments that add no value.

## Reference-first rule

Before creating a new agent or skill in this repo:

1. Check `https://github.com/github/awesome-copilot`.
2. Search the published catalog first:
   - `https://awesome-copilot.github.com/agents`
   - `https://awesome-copilot.github.com/skills`
   - `https://awesome-copilot.github.com/llms.txt`
3. Reuse or adapt a close example instead of inventing a new pattern from scratch.

Use the upstream repo as the template source for frontmatter, naming,
checklists, and bundled-asset patterns.

## Repo AI surfaces

| Surface | Purpose |
| --- | --- |
| `.github/copilot-instructions.md` | Repo-wide Copilot behavior and implementation defaults |
| `.github/skills/<skill>/SKILL.md` | Repo runtime skills used by Copilot in this workspace |
| `agents/*.agent.md` | Shareable custom agents for repo-specific workflows |
| `.github/extensions/` | Copilot CLI extensions and canvas/runtime automation |

This repo keeps runtime skills under `.github/skills/` rather than a root
`skills/` folder so the workspace can load them directly.

## Authoring standards

### Agents

- Use lowercase-hyphen filenames with the `.agent.md` suffix.
- Include markdown frontmatter with, at minimum, `name` and `description`.
- Prefer adding `model` and `tools` when the target platform supports them.
- State the agent's scope, priorities, and constraints explicitly.
- Optimize for high-signal behavior, not novelty or persona for its own sake.

### Skills

- Use a lowercase-hyphen folder name containing `SKILL.md`.
- Include frontmatter with `name` and a clear `description`.
- Define trigger conditions, workflow phases, output contract, and gotchas.
- Keep bundled assets small and reference them from the skill document.
- Prefer task-focused skills over generic "do everything" prompts.

## Weatherapp engineering rules

### Backend

- Python 3.12, FastAPI, pytest, and Ruff are the default backend toolchain.
- All async backend code uses `asyncio`.
- Keep NWS API access inside the backend service layer; route handlers should
  not call NWS directly.
- Reuse `_mps_to_mph`, `_c_to_f`, `_wind_direction`, and `_parse_wind_values`
  when those conversions apply.

### Frontend

- TypeScript, React, and Vite are the default frontend stack.
- Preserve proxy-based local API behavior unless the change intentionally
  updates the local development contract.
- Keep UI state transitions, stale-data warnings, and refresh behavior coherent.

### Documentation and operations

- Never place secrets, passwords, tokens, or real credentials in source,
  prompts, examples, templates, or logs. Use placeholders such as `ask admin`.
- Any behavior-changing change should include the smallest relevant tests and
  update user-facing or operator-facing docs when the contract changes.

## Review expectations

- Use GitHub Flow with short-lived branches and pull requests into `main`.
- Use Conventional Commits for commit messages.
- Keep PRs scoped to one concern when possible.
- Require a human review before merge.
- When adding or updating agents or skills, cite the upstream `awesome-copilot`
  example used as a starting point in the PR description.

## Related docs

- `CONTRIBUTING.md`
- `.github/copilot-instructions.md`
- `.github/skills/weatherapp-local-preflight/SKILL.md`
- `agents/weatherapp-code-review.agent.md`
