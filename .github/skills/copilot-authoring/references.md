# Agentic resource catalogue

Append new resources under the matching heading with a one-line note. Do not
duplicate existing entries.

## Research

- [Agentic Context Engineering (ACE), arXiv 2510.04618](https://arxiv.org/html/2510.04618v3)
  — Context as an evolving playbook; Generator → Reflector → Curator with
  small itemized delta updates to avoid brevity bias and context collapse. We
  adopt the loop only (field notes → curator), not the full framework.
- [Evaluating AGENTS.md, arXiv 2602.11988](https://arxiv.org/html/2602.11988v3)
  — In the study's evaluated settings, context files did not generally improve
  task success and increased inference cost by over 20% on average. Repository
  overviews were not helpful, and agents followed explicit instructions. Keep
  `AGENTS.md` to non-discoverable rules.

## Skill authoring

- [Anthropic: Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
  — Concise SKILL.md under 500 lines; third-person what + when descriptions;
  references one level deep; build from observed failures and evaluations.
- [GitHub: Agent skills](https://docs.github.com/en/copilot/concepts/customizations/agent-skills)
  — Supported skill locations and surfaces.
- [GitHub: Adding agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)
  — `SKILL.md` frontmatter (`name`, `description`, `license`,
  `allowed-tools`) and bundled scripts.

## Custom agents and subagents

- [GitHub: Custom agents configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
  — Supported frontmatter, tool aliases, 30,000-character prompt limit,
  retired `infer`.
- [GitHub: Invoking custom agents in Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/invoke-custom-agents)
  — `/agent` and `copilot --agent <id>`; agent locations by scope.
- [GitHub: Creating custom agents for Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli)
  — `include-custom-instructions: true` opts subagents into repository
  instructions; `--no-custom-instructions` overrides it.
- [GitHub: Custom agents (concepts)](https://docs.github.com/en/copilot/concepts/customizations/custom-agents)
  — Session agent vs subagent; CLI custom subagents do not get repository
  instructions by default.
- [GitHub: Customizing the GitHub Copilot app](https://docs.github.com/en/copilot/how-tos/github-copilot-app/customize-github-copilot-app)
  — Agent picker and `/agent` in the app; skills availability.
- [GitHub: Creating custom agents for Copilot cloud agent](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/create-custom-agents)
  — Repository agents appear on GitHub.com after merge to the default branch.
- [GitHub: Using subagents](https://docs.github.com/en/copilot/how-tos/copilot-in-your-ide/use-copilot-agents/use-subagents)
  — Subagents run in isolated context and cannot create other subagents;
  VS Code agent tool lists need `runSubagent` for delegation.

## Instructions, memory, and customization

- [GitHub: Adding repository custom instructions](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/add-custom-instructions/add-repository-instructions)
  — `.github/instructions/**/NAME.instructions.md` with `applyTo` globs and
  optional `excludeAgent`; on GitHub.com, cloud agent and code review only.
- [GitHub: Customization cheat sheet](https://docs.github.com/en/copilot/reference/customization-cheat-sheet)
  — Which customization (instructions, agents, skills, hooks, MCP) fits which
  job, and where each file lives.
- [GitHub: Copilot Memory](https://docs.github.com/en/copilot/concepts/prompting-and-context/copilot-memory)
  — Repository facts and user preferences captured automatically; keep in
  `AGENTS.md` what memory and code cannot reliably infer.

## Issue forms and PR templates

- [GitHub: Syntax for issue forms](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms)
  — YAML form location, required keys, input types, and validations; not
  supported for pull requests; default `labels` must already exist.
- [GitHub: Creating a pull request template](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/creating-a-pull-request-template-for-your-repository)
  — Markdown template locations, multiple templates, and default-branch
  availability.

## Prior art

- [github/awesome-copilot](https://github.com/github/awesome-copilot)
  ([agents](https://awesome-copilot.github.com/agents/),
  [skills](https://awesome-copilot.github.com/skills/),
  [llms.txt](https://awesome-copilot.github.com/llms.txt)) — Check for a close
  upstream pattern before authoring a new artifact.
