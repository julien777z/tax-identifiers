---
description: Project conventions and workflow rules.
alwaysApply: true
---

# Project Rules

## Version Bumps

- Never edit `version` in `pyproject.toml`. CI owns it.
- The `Publish to PyPI` workflow bumps the version with `poetry version <increment>`, then commits and tags the result. A manual bump in a PR collides with that commit.
- To release, dispatch the `Publish to PyPI` workflow and choose `patch`, `minor`, or `major`. If a change is breaking, say so in the PR description so the right increment is picked. Do not encode it in the version yourself.
