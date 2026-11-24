---
name: field-notes
description: "Records a short field note in the current session's files folder when an agent or skill was wrong or blocked and a fix was found, a tool or command was retried with changes, the user corrected the agent, or guidance was missing or stale. Never writes to the repository."
---

# Field Notes

Capture what happened while it is still fresh so a curator can later make a
small, itemized improvement to the owning agent, skill, or `AGENTS.md`.

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
repo: owner/name          owner: <agent-or-skill-file or AGENTS.md>
kind: wrong | blocked | repeated-tool | user-correction | missing-guidance
trigger: what happened (1-3 lines)
fix: what worked
proposed change: one itemized add/edit/remove for the owner file
evidence: commands, errors, PR/issue links
status: new
```

## Rules

- `owner` is the file that should change (for example
  `.github/agents/<name>.agent.md`, `.github/skills/<name>/SKILL.md`, or
  `AGENTS.md`).
- `proposed change` is one concrete add, edit, or remove. Split unrelated
  lessons into separate notes.
- Keep `evidence` factual: exact commands, error text, and links. Remove
  secrets, tokens, and private host data.
- Leave `status: new`. The curator updates it after merging the change.
