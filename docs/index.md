# pup-up

<img src="images/pup.png" alt="pup-pack logo" width="110">

`pup-up` brings a Python repository up to a managed professional baseline.

It is designed for repositories that follow repeatable professional patterns
but still contain local, project-specific work.
The tool updates shared repository infrastructure from canonical templates
while preserving source code, tests, notebooks, data, documentation,
and other project-specific surfaces unless those areas are explicitly managed.

## Purpose

Many professional Python repositories share the same infrastructure:

- editor and Git configuration
- ignore and line-ending rules
- Markdown, YAML, and link-checking configuration
- Python tooling configuration
- documentation tooling configuration
- continuous integration workflows
- release and package validation surfaces

Keeping those files synchronized by hand is error-prone.
`pup-up` makes the shared parts explicit, repeatable, and reviewable.

## Design Model

`pup-up` separates repository maintenance into three concerns:

1. **Canonical templates** define the standard files and managed content.
2. **Repository conventions** identify the target repository shape and applicable template layers.
3. **Repository-specific surfaces** remain local to the project and require human review.

The tool is intentionally conservative.
It updates files that are known to be managed and reports
the areas that require human judgment.

## Template Layers

Templates are applied as ordered layers.
Later layers may override files from earlier layers.

The standard layer model increases in specificity:

- `ALL` for files shared by all repositories.
- `ALL-PY` for Python repository tooling.
- `ALL-PY-SRC` for Python repositories with a `src/` package layout.
- `ALL-PY-SRC-PYPI` for publishable Python `src/` package repositories.

Layers are additive across managed files while allowing a more specific
layer to supersede an earlier version of the same file.

## Managed and Preserved Surfaces

A managed surface is a file that can be updated from the canonical baseline.

A preserved surface is project-specific and
should not be overwritten automatically.
Examples include source code, tests, notebooks, data files,
SQL files, and project-specific documentation.

## See Also

- [API](./api.md)
