---
description: Project conventions and workflow rules.
alwaysApply: true
---

# Project Rules

## Clarifying Questions

- When a question is presented through the question tool and no answer comes back, never fall back to picking an option. Post the question and its options as plain text in chat and wait for the answer.

## PR Monitoring And Background Timers

- Never poll a PR with background `sleep` or timed self check-ins; act only on delivered PR activity webhooks.

## Documentation

- Document current behavior only. Never describe what a symbol used to do, what was removed, renamed, or deprecated, and never write migration tables or upgrade notes.
- This project has a single known consumer, so there is no external audience for a deprecation path. Git history is the record of what changed; the README describes what exists now.
- The same applies to code comments and docstrings: no "formerly", "replaces", or "kept for backwards compatibility" notes.

## Version Bumps

- Never edit `version` in `pyproject.toml`. CI owns it.
- The `Publish to PyPI` workflow bumps the version with `poetry version <increment>`, then commits and tags the result. A manual bump in a PR collides with that commit.
- To release, dispatch the `Publish to PyPI` workflow and choose `patch`, `minor`, or `major`. If a change is breaking, say so in the PR description so the right increment is picked. Do not encode it in the version yourself.
