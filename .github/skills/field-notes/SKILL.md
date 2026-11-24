---
name: field-notes
description: "Records a short field note in the current session's files folder when an agent or skill was wrong or blocked and a fix was found, a tool or command was retried with changes, the user corrected the agent, or guidance was missing or stale. Never writes to the repository."
---

# Field Notes

Capture what happened while it is still fresh so a curator can later make a
small, itemized improvement to the owning agent, skill, `AGENTS.md`, or
guidance record.

Source: original to this baseline; the reflect-then-curate loop is a
lightweight adaptation of the ACE paper's reflector and curator roles.

## Triggers

Write one note when any of these happen:

- An agent or skill was wrong or blocked and a fix was found.
- The same tool or command was retried with changes before it worked.
- The user corrected the agent.
- Guidance was missing or stale.

Do not write notes for routine success, expected failures that the workflow
already handles, or speculation without evidence.

## Location

Write only to the current session's files folder:

```text
<session-state>/<session-id>/files/field-notes/YYYYMMDD-HHMM-<slug>.md
```

Use the session artifacts/files directory provided by the runtime. Never write
field notes inside the repository checkout, and never commit them.

## Format

Use exactly these fields, one note per file:

```text
repo: owner/name
owner: <agent-or-skill-file, AGENTS.md, or guidance record>
kind: wrong | blocked | repeated-tool | user-correction | missing-guidance
trigger: what happened (1-3 lines)
fix: what worked
proposed change: one itemized add/edit/remove for the owner file
evidence: commands, errors, PR/issue links
status: new
```

## Rules

- `owner` is the file to add or change (for example
  `.github/agents/<name>.agent.md`, `.github/skills/<name>/SKILL.md`,
  `AGENTS.md`, or a `guidance/` record).
- `proposed change` is one concrete add, edit, or remove. Split unrelated
  lessons into separate notes.
- Keep `evidence` factual: exact commands, error text, and links. Redact
  secrets, tokens, personal data, and private host data from the note.
- Leave `status: new`. The curator sets `status: curated <date> <PR>` after
  verifying a draft PR. Until then, the note remains pending.

## References

- [Agentic Context Engineering (ACE)](https://arxiv.org/html/2510.04618v3):
  generator, reflector, and curator roles with itemized delta updates.
- [Agent Skills best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices):
  concise skills that are evaluated and refined from observed use.
- [About agent skills](https://docs.github.com/en/copilot/concepts/customizations/agent-skills):
  GitHub Copilot skill format and locations.
