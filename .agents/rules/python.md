---
description: Python code conventions.
alwaysApply: true
---

# Python Rules

## Docstrings And Comments

- No module-level docstrings. Docstrings go on classes, methods and functions only.
- Every class, method and function has a docstring, followed by a blank line before the body.
- Do not write comments that narrate the code. Add one only when the reason for a line is not recoverable from the line itself.
- Never write "formerly", "replaces", "kept for backwards compatibility", or any other note about what the code used to do.

## Types

- Field types must be valid type expressions. A call is never allowed in annotation position, and neither is a variable assigned from a call — so a field type is a plain `Annotated` alias, never a factory that returns one.
- Put configuration in metadata objects inside `Annotated`, where calls are legal.
- `pyright` runs over the package, the tests and the scripts in CI and must report zero errors.

## Style

- Line length 110, `black` formatting, `isort` with the `black` profile.
- Absolute `tax_identifiers.*` imports only; no relative imports.
