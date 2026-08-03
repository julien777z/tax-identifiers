---
description: Rules that hold in every repository, regardless of its stack or conventions.
alwaysApply: true
---

# Global Rules

## Agent Prompts

- In repositories that provide an agent CLI or otherwise interact with agents, store every agent prompt in a dedicated Markdown file rather than inline in application code so it is easy to find, review, and maintain. Application code may load a prompt file and interpolate runtime values into it.

## User Approvals

- After initiating an approval that requires user interaction, wait up to 10 minutes without polling or interacting with the approval surface.
- Treat it as failed only after that window or an explicit failure from the user.
- A failure is not approval; wait until the user resumes the task before prompting again.

## Documentation

- Document current behavior only. Never describe what a symbol used to do, what was removed,
  renamed, or deprecated, and never write migration tables or upgrade notes.
- Git history is the record of what changed; documentation describes what exists now.
- The same applies to code comments and docstrings: no "formerly", "replaces", or "kept for
  backwards compatibility" notes.

## Clarifying Questions

- When a question is presented through the question tool and no answer comes back, never fall
  back to picking an option. Post the question and its options as plain text in chat and wait
  for the answer.

## PR Monitoring And Background Timers

- Never poll a PR with background `sleep` or timed self check-ins; act only on delivered PR
  activity webhooks.
