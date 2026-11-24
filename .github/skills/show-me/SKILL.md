---
name: show-me
description: "Explain the current topic visually with a focused diagram, code sketch, or interactive visual. Use when the user asks to see how something works or how a change fits together."
disable-model-invocation: true
---

# Show me

Turn the current question into a compact visual explanation. This skill is for
understanding a topic, not for changing the application.

## Workflow

1. Identify the question, audience, and relevant scope from the conversation.
   Inspect the smallest set of source files or documentation needed to verify
   the explanation. If information is missing, label the uncertainty.
2. Choose the simplest representation that answers the question:
   - Use pseudocode for decisions or an algorithm.
   - Use a call tree, component tree, or file tree for ownership and structure.
   - Use Mermaid for interactions, sequences, or data flow.
   - Use a focused diff for a before-and-after change, or a complete block when
     the surrounding context is needed to understand or copy the result.
   - For a layout, comparison, or concept that needs richer presentation, create
     a small self-contained HTML visual. Use real labels and verified data,
     adapt the relevant product styling, and make it usable on desktop and
     mobile. Put temporary artifacts in the session workspace, not the repo.
3. Keep each visual close to its short explanation. Include only boundaries,
   states, paths, and details that matter to the question; use multiple views
   only when they clarify different points.
4. If an HTML visual is created, open it in an available browser preview or
   provide an accessible artifact link. If neither is available, state where
   the file is and how the user can view it; do not claim it was opened.

## Output contract

- Deliver a readable visual and a concise explanation of its key point.
- Ground current behavior in the inspected implementation and distinguish
  proposed changes from existing behavior.
- Mention relevant unknowns rather than inventing flow, data, or implementation.
- Do not expose credentials, tokens, personal information, or private data in
  diagrams or artifacts. Do not send repository content to external services.
