# pup-up: Professional Python Project Updater

[![PyPI](https://img.shields.io/pypi/v/pup-up?logo=pypi&label=pypi)](https://pypi.org/project/pup-up/)
[![Docs Site](https://img.shields.io/badge/docs-site-blue?logo=github)](https://pup-pack.github.io/pup-up/)
[![Repo](https://img.shields.io/badge/repo-GitHub-black?logo=github)](https://github.com/pup-pack/pup-up)
[![Python 3.15](https://img.shields.io/badge/python-3.15%2B-blue?logo=python)](https://github.com/pup-pack/pup-up/blob/main/pyproject.toml)
[![uv managed](https://img.shields.io/badge/uv-managed-DE5FE9)](https://docs.astral.sh/uv/)
[![ty type checked](https://img.shields.io/badge/ty-type_checked-2F80ED)](https://docs.astral.sh/ty/)
[![Zensical docs](https://img.shields.io/badge/Zensical-docs-purple)](https://zensical.org/)
[![MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](https://github.com/pup-pack/pup-up/blob/main/LICENSE)

[![CI](https://github.com/pup-pack/pup-up/actions/workflows/ci-python-zensical.yml/badge.svg?branch=main)](https://github.com/pup-pack/pup-up/actions/workflows/ci-python-zensical.yml)
[![Docs-Deploy](https://github.com/pup-pack/pup-up/actions/workflows/deploy-zensical.yml/badge.svg?branch=main)](https://github.com/pup-pack/pup-up/actions/workflows/deploy-zensical.yml)
[![Pre-Release](https://github.com/pup-pack/pup-up/actions/workflows/pre-release.yml/badge.svg?branch=main)](https://github.com/pup-pack/pup-up/actions/workflows/pre-release.yml)
[![Release](https://github.com/pup-pack/pup-up/actions/workflows/release-pypi.yml/badge.svg)](https://github.com/pup-pack/pup-up/actions/workflows/release-pypi.yml)
[![Links](https://github.com/pup-pack/pup-up/actions/workflows/links.yml/badge.svg?branch=main)](https://github.com/pup-pack/pup-up/actions/workflows/links.yml)
[![Dependabot](https://img.shields.io/badge/Dependabot-enabled-brightgreen.svg)](https://github.com/pup-pack/pup-up/security)

<img
src="https://raw.githubusercontent.com/pup-pack/pup-up/main/docs/images/pup.png"
alt="pup logo"
width="110">

> Opinionated professional Python project template synchronizer

## Purpose

Professional Python repositories commonly share infrastructure such as:

- editor and Git configuration
- ignore and line-ending rules
- Markdown, YAML, and link checking
- formatting, linting, type checking, and testing
- documentation tooling
- continuous integration
- package and release validation

`pup-up` makes it easy to keep the infrastructure files commonly used in
professional projects current and consistent.

## Benefits

`pup-up` is **pull-based**.
Each repository fetches the current baseline and applies it on its own terms.
Nothing reaches in from a central place, so:

- **Repo owner is in control.** Run it when you choose. The default is a dry run;
  nothing is written until you pass `--write`.
- **See before accept.** `--diff` shows exactly what would change,
  line by line, before any file is touched.
- **Blast radius is one repo.** A template change is applied per repository.
- **Local differences survive.** A repo that needs to diverge just doesn't
  take a specific file. Templates offer an optional baseline, never a mandate.

Templates are fetched by **immutable commit SHA**,
so an update always reflects the latest push to the template repository
and every run is pinned to an exact template commit.

Repo type is inferred from the presence of key files
so no extensive configuration is needed.
For example:

- ALL REPOS
- `pyproject.toml` indicates ALL PY REPOS
- `pyproject.toml` + `src` indicates ALL PY SRC REPOS
- `pyproject.toml` + `src` + `[build-system]` + `[tool.hatch.version]` + `[project.urls]`
  indicates ALL PY SRC PYPI REPOS

## Default Template Source

- [templates](https://github.com/pup-pack/templates)

## Update a Repo based on Templates

```shell
# see what files would change (dry run, the default)
uvx pup-up

# run the latest published version in dry-run mode
uvx pup-up@latest

# see exactly what would change, line by line
uvx pup-up --diff

# add and overwrite all the files listed (CAUTION: DESTRUCTIVE)
uvx pup-up --write

# add and overwrite only specific files listed (CAUTION: DESTRUCTIVE)
uvx pup-up --write .gitattributes .github/.yamllint.yml .github/workflows/links.yml
```

## Developer Command Reference

<details>
<summary>Show command reference</summary>

### In a machine terminal

Open a machine terminal where you want the project:

```shell
git clone https://github.com/pup-pack/pup-up

cd pup-up
code .
```

### In a VS Code terminal

```shell
uv self update
uv python pin 3.15
uv python install
uv lock --upgrade
uv sync

uv run pre-commit install
uv run pre-commit autoupdate

git add -A
uv run pre-commit run --all-files
# repeat if changes were made
uv run pre-commit run --all-files

# run locally to test
uv run pup-up
uv run pup-up --diff
uv run pup-up --write
uv run pup-up --write .gitattributes .github/.yamllint.yml .github/workflows/links.yml

# types, tests, docs
uv run ty check
uv run python -m pytest
uv run python -m zensical build

# save progress
git add -A
git commit -m "update"
git push -u origin main
```

</details>

## Documentation

- [Documentation](https://pup-pack.github.io/pup-up/)

## Annotations

[.annotations/annotations.md](https://github.com/pup-pack/pup-up/blob/main/.annotations/annotations.md)

## Citation

[CITATION.cff](https://github.com/pup-pack/pup-up/blob/main/CITATION.cff)

## License

[MIT](https://github.com/pup-pack/pup-up/blob/main/LICENSE)
