---
alwaysApply: true
---

# Poetry Project Rules

## Project Configuration

- Preserve the package's declared Python 3.11–3.14 compatibility and use Poetry 2.x with PEP 621 `[project]` metadata; keep `[tool.poetry]` only for package/include configuration that PEP 621 does not express.
- Declare runtime dependencies in `[project.dependencies]`, development dependencies in `[project.optional-dependencies].dev`, and console entry points in `[project.scripts]`.
- Configure strict Pyright, pytest, and Black with the repository's 110-character line length and declared Python targets.
- Keep the Poetry build system at the end of `pyproject.toml`:

```toml
[build-system]
requires = ["poetry-core>=2.0.0"]
build-backend = "poetry.core.masonry.api"
```

- Use `poetry install`, `poetry run black .`, `poetry run pyright`, and `poetry run pytest` for the standard local workflow.

## Application Structure

- Prefer separate focused modules over monoliths, organizing code under `clients/`, `services/`, `models/`, and `core/` as applicable.
- Use syntax supported by the package's full declared Python compatibility range.
- Give every function and class a one-line imperative docstring followed by a blank line.
- Services may be plain functions. Pass clients, sessions, and configuration explicitly rather than storing module-level runtime globals.
- Configure logging centrally and use it instead of `print()`.

## Testing

- Use pytest with small, readable tests.
- Prefer dependency injection or fakes over deep patching.

## Guardrails

- Use Black rather than Ruff for formatting.
- Keep comments minimal and do not generate additional Markdown beyond the existing rules and Project Layout documents unless the user requests it.
