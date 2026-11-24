---
name: copilot-authoring
description: "Authoring standards for Copilot customizations in this repo: AGENTS.md, custom agents, skills, and instructions. Use when creating, editing, or reviewing an agent, skill, or instruction file, or when the user shares a new agentic resource to catalogue."
---

# Copilot authoring

Keep customizations small, sourced, and backed by real use. Check
[references.md](references.md) for the official formats before writing.

## Before you write

1. Prefer editing an existing agent, skill, or `AGENTS.md` over adding a new
   file.
2. Create a new skill only when a field note or observed failure shows the
   need. Cite that evidence in the PR.
3. Check `github/awesome-copilot` for a close example and name it in the PR.

## Locations and formats

| Artifact | Location | Required frontmatter |
| --- | --- | --- |
| Repo rules | `AGENTS.md` | none |
| Copilot pointer | `.github/copilot-instructions.md` | none |
| Custom agent | `.github/agents/<name>.agent.md` | `description` |
| Skill | `.github/skills/<name>/SKILL.md` | `name`, `description` |

- Agent frontmatter: use only documented properties (`name`, `description`,
  `target`, `tools`, `model`, `disable-model-invocation`, `user-invocable`,
  `mcp-servers`, `metadata`). `infer` is retired; use
  `disable-model-invocation` and `user-invocable`. `handoffs` and
  `argument-hint` are ignored on GitHub.com. Prompt body max 30,000 characters.
- Grant the fewest tools that still let the agent finish its workflow; omit
  `tools` only when the agent needs everything (for example, an orchestrator).
- Subagents cannot create subagents. Agents meant to run as subagents must work
  from the context they are given.
- Skill `name`: lowercase letters, numbers, and hyphens; matches the folder.
- Skill `description`: third person, says what the skill does and when to use
  it.
- Keep `SKILL.md` under 500 lines; move detail into files linked one level
  deep from `SKILL.md`.

## Writing rules

- `AGENTS.md` holds only rules an agent cannot work out from the code, README,
  or docs. No repo overviews or directory tours.
- Use consistent terms, concrete commands, and no time-sensitive statements.
- Never include secrets or real credentials; use placeholders such as
  `ask admin`.
- Cite the official doc or research behind any new rule in the PR.

## Resource catalogue

When the user shares a new agentic resource (paper, doc, guide), append it to
[references.md](references.md) under the matching section with a one-line note
on why it matters. Do not duplicate existing entries.
