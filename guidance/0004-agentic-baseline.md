# 0004: Lightweight agentic baseline

## Status
Accepted

## Context
Copilot customizations had drifted: a review agent lived in the root `agents/`
folder, which is not a supported repository agent location, and there was no
default entry agent or feedback loop. Research shows repository overviews in
context files add cost without improving results, while explicit rules are
followed.

## Decision
- `AGENTS.md` is canonical and holds only rules an agent cannot work out from
  the code or docs. `.github/copilot-instructions.md` points to it.
- Three repository agents in `.github/agents/`: `weatherapp-main` (default
  entry agent, delegates one hop), `weatherapp-test`, and `weatherapp-deploy`.
- No custom code-review agent; pull requests use built-in Copilot code review
  on GitHub.
- The `field-notes` skill records lessons in the session files folder, never
  the repo. A curator later turns them into small itemized PRs.
- The `copilot-authoring` skill holds authoring standards and the resource
  catalogue. New skills are added only when a field note or failure shows the
  need.

## Consequences
- Same shape as `dylanwhitetech/nailed-it-kitchen` and
  `dylanwhitetech/k3s-infrastructure`, so one curator can maintain all three.
- The default agent cannot be enforced by files; contributors select
  `weatherapp-main` in the app or CLI (see `CONTRIBUTING.md`).

## References
- [AGENTS.md](../AGENTS.md)
- [.github/skills/copilot-authoring/references.md](../.github/skills/copilot-authoring/references.md)
- [Evaluating AGENTS.md, arXiv 2602.11988](https://arxiv.org/html/2602.11988v3)
- [Agentic Context Engineering, arXiv 2510.04618](https://arxiv.org/html/2510.04618v3)
- [GitHub custom agents configuration](https://docs.github.com/en/copilot/reference/custom-agents-configuration)
