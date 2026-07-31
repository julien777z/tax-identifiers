---
description: Rules that hold in every repository, regardless of its stack or conventions.
alwaysApply: true
---

# Global Rules

## Clarifying Questions

- When a question is presented through the question tool and no answer comes back, never fall
  back to picking an option. Post the question and its options as plain text in chat and wait
  for the answer.

## PR Monitoring And Background Timers

- Never poll a PR with background `sleep` or timed self check-ins; act only on delivered PR
  activity webhooks.
