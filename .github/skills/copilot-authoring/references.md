# Agentic resource catalogue

Append new resources under the matching section with a one-line note.

## Research

- [Agentic Context Engineering (ACE), arXiv 2510.04618](https://arxiv.org/html/2510.04618v3):
  context as an evolving playbook (generator, reflector, curator) updated with
  small itemized deltas instead of full rewrites. We use the loop only:
  field notes are the reflector output; the curator applies deltas.
- [Evaluating AGENTS.md, arXiv 2602.11988](https://arxiv.org/html/2602.11988v3):
  repository overviews in context files did not improve task success and
  raised cost by about 20%; agents do follow stated instructions. Keep
  `AGENTS.md` to non-discoverable rules.

## Skill authoring

- [Anthropic: Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices):
  concise skills, third-person what-and-when descriptions, `SKILL.md` under
  500 lines, references one level deep, build evaluations from real failures.
- [GitHub: Agent skills](https://docs.github.com/en/copilot/concepts/customizations/agent-skills):
  supported skill locations and surfaces.
- [GitHub: Adding agent skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills):
  `SKILL.md` frontmatter (`name`, `description`, `license`, `allowed-tools`).

## Custom agents

- [GitHub: Custom agents](https://docs.github.com/en/copilot/concepts/customizations/custom-agents):
  what custom agents are and where they apply.
- [GitHub: Custom agents configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration):
  supported frontmatter, tool aliases, retired `infer`, 30,000-character
  prompt limit.
- [GitHub: Using subagents](https://docs.github.com/en/copilot/how-tos/copilot-in-your-ide/use-copilot-agents/use-subagents):
  subagents run in an isolated context and cannot create other subagents.
- [GitHub: Invoking custom agents in Copilot CLI](https://docs.github.com/en/copilot/how-tos/copilot-cli/use-copilot-cli/invoke-custom-agents):
  `/agent` and `copilot --agent=<name>`.
- [GitHub: Customizing the GitHub Copilot app](https://docs.github.com/en/copilot/how-tos/github-copilot-app/customize-github-copilot-app):
  agent picker, `/agent`, and repository instructions in the app.

## Context and memory

- [GitHub: Copilot customization cheat sheet](https://docs.github.com/en/copilot/reference/customization-cheat-sheet):
  which customization type to use for which job.
- [GitHub: Copilot Memory](https://docs.github.com/en/copilot/concepts/prompting-and-context/copilot-memory):
  repository facts captured automatically with citations; keep explicit rules
  in `AGENTS.md`.

## Examples

- [github/awesome-copilot](https://github.com/github/awesome-copilot)
  ([agents](https://awesome-copilot.github.com/agents),
  [skills](https://awesome-copilot.github.com/skills),
  [llms.txt](https://awesome-copilot.github.com/llms.txt)): community examples
  to adapt before writing new agents or skills.
