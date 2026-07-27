---
description: Project conventions and workflow rules.
alwaysApply: true
---

# Project Rules

## PR Monitoring And Background Timers

- Never poll a PR with background `sleep` or timed self check-ins; act only on delivered PR activity webhooks.

## Version Bumps

- Never edit `version` in `pyproject.toml`. CI owns it.
- The `Publish to PyPI` workflow bumps the version with `poetry version <increment>`, then commits and tags the result. A manual bump in a PR collides with that commit.
- To release, dispatch the `Publish to PyPI` workflow and choose `patch`, `minor`, or `major`. If a change is breaking, say so in the PR description so the right increment is picked — do not encode it in the version yourself.
