---
name: copilot-authoring
description: "Applies verified authoring standards for Copilot custom agents, skills, custom instructions, AGENTS.md, GitHub issue forms, and PR templates, and maintains the agentic resource catalogue. Use when creating, editing, or reviewing AGENTS.md, .github/agents/, .github/skills/, .github/copilot-instructions.md, .github/instructions/*.instructions.md, .github/ISSUE_TEMPLATE/*.yml or *.yaml, or pull_request_template.md and PULL_REQUEST_TEMPLATE/ under the root, docs/, or .github/, or when the user shares a new agentic resource."
---

# Copilot Authoring

Keep agentic resources small, accurate, and grounded in official docs. Check
[references.md](references.md) before adding or changing an artifact; cite
the sources you used in the PR description.

Source: original to this baseline; rules are summarized from the official
GitHub and Anthropic docs listed under References.

## Before you add anything

1. Create a new skill only when a field note or observed failure
   shows the need. Prefer editing an existing agent or skill.
2. Check `github/awesome-copilot` for a close upstream pattern first and reuse
   it (reference-first rule in `AGENTS.md`).
3. Verify every format claim against the official docs in `references.md`. Do
   not invent frontmatter fields.

## Locations

| Artifact | Location |
| --- | --- |
| Canonical repo rules | `AGENTS.md` |
| Copilot pointer | `.github/copilot-instructions.md` |
| Path-specific instructions | `.github/instructions/**/<name>.instructions.md` |
| Custom agents | `.github/agents/<name>.agent.md` |
| Skills | `.github/skills/<name>/SKILL.md` (+ files one level deep) |
| Issue forms | `.github/ISSUE_TEMPLATE/<name>.yml` (or `.yaml`) |
| PR templates | `pull_request_template.md` or `PULL_REQUEST_TEMPLATE/*.md` under the root, `docs/`, or `.github/` |
| Durable decisions | `guidance/NNNN-<slug>.md` |

A root `agents/` folder is not a repository agent location.

## Attribution

- Agent, skill, and instruction prose adapted from an upstream file starts
  with a `Source:` line linking the exact upstream file. Prose written from
  scratch says so on its `Source:` line, and the PR notes that no upstream
  fit existed.
- List the official docs relied on under the file's `## References`.
- Issue forms and PR templates have no attribution field; cite their sources
  in authoring instructions or the PR, never as unsupported template keys.

## Custom agents

- Frontmatter: `description` (required), optional `name`, `tools`, `model`,
  `target`, `disable-model-invocation`, `user-invocable`, `mcp-servers`,
  `metadata`.
- In Copilot CLI, `include-custom-instructions: true` opts a custom subagent
  into repository instructions unless `--no-custom-instructions` is set.
- `infer` is retired; use `disable-model-invocation` and `user-invocable`.
- `handoffs` and `argument-hint` are ignored on GitHub.com; do not rely on
  them for required behavior.
- Omit `model` to inherit the default. If you pin one, state the reason in
  the agent body or PR.
- Prompt body maximum is 30,000 characters. Keep it far shorter.
- Grant the least tools needed. Use aliases: `read`, `edit`, `search`,
  `execute`, `agent`, `web`, `todo`. Omit `tools` only when the agent needs
  everything (for example, an orchestrator).
- For agents that delegate in VS Code and specify a `tools` list, include
  `runSubagent`.
- One hop: subagents cannot create subagents. In Copilot CLI, custom
  subagents do not receive repository instructions by default. The main agent
  gives each subagent complete context and a bounded objective.
- No file sets a default agent; users select one per session (`/agent`,
  `copilot --agent <id>`, or the agent picker).

## Skills

- Frontmatter: `name` (required; lowercase letters, numbers, hyphens; max 64;
  matches the folder) and `description` (required; max 1,024). Optional:
  `license`, `allowed-tools`. Do not pre-approve `shell`/`bash` in
  `allowed-tools` unless the skill and its scripts are fully trusted.
- Write `description` in third person and state what the skill does and when
  to use it.
- Keep `SKILL.md` under 500 lines; move detail into files one level deep.
- Use consistent terminology. Avoid time-sensitive information.
- Assume the model is capable; add only context it does not already have.

## AGENTS.md and custom instructions

- `AGENTS.md` holds rules an agent cannot work out from code, README, or
  Copilot Memory: safety constraints, approvals, non-obvious conventions.
- Do not add repository overviews or directory tours.
- `.github/copilot-instructions.md` stays a thin pointer to `AGENTS.md`.
- Path-specific `*.instructions.md` files need `applyTo` frontmatter with
  one or more comma-separated globs. On GitHub.com they apply only to Copilot
  cloud agent and code review; optional `excludeAgent: "code-review"` or
  `"cloud-agent"` drops one of them. Check the IDE docs before relying on
  them elsewhere.

## Issue forms and PR templates

- Verify formats against the GitHub docs below; issue-form YAML is not
  supported for pull requests.
- Issue forms require `name`, `description`, and a `body` array. Use documented
  input types, attributes, and validations; parse YAML and check the schema,
  not just syntax.
- When editing a form, keep its purpose and required fields unless the change
  is intentional. Verify that any changed default `labels` exist in the
  target repository; missing labels are not added.
- PR templates are Markdown. Preserve the repository's existing headings,
  comments, and checklists when filling them out; keep requested evidence
  accurate. Templates become available after merge to the default branch.

## Changing resources

- Make small, itemized add/edit/remove changes; never rewrite a whole file to
  absorb one lesson.
- Cite the field note, failure, or doc that motivated each change.
- Ship guidance or doc updates in the same PR as the behavior change.
- After renaming or removing an agent or skill, update the `AGENTS.md`
  roster and search the repo for stale references.
- Never include secrets or real credentials; use placeholders such as
  `ask admin`.

## Resource catalogue

When the user shares a new agentic resource (paper, doc, or guide), append it
to [references.md](references.md) under the right heading with a one-line
note on why it matters. Do not duplicate existing entries.

## References

Full catalogue with notes: [references.md](references.md).

- [Custom agents configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
- [Create custom agents for Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli)
- [Use subagents in your IDE](https://docs.github.com/en/copilot/how-tos/copilot-in-your-ide/use-copilot-agents/use-subagents)
- [About agent skills](https://docs.github.com/en/copilot/concepts/customizations/agent-skills)
- [Adding repository custom instructions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions)
- [Customization cheat sheet](https://docs.github.com/en/copilot/reference/customization-cheat-sheet)
- [Agent Skills best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Evaluating AGENTS.md (arXiv 2602.11988)](https://arxiv.org/html/2602.11988v3)
- [Syntax for issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
- [Creating a pull request template](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository)
