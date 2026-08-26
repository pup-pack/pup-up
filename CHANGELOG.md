# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to this project will be documented in this file.

The format is based on **[Keep a Changelog](https://keepachangelog.com/en/1.1.0/)**
and this project adheres to **[Semantic Versioning](https://semver.org/spec/v2.0.0.html)**.

---

## [Unreleased]

---

## [0.2.0] - 2026-08-26

### Added

- Support for additive template layers including `ALL-PY-SRC-PYPI`.
- Protected-path handling for managed repository files.
- Stable file read and write errors for managed-file operations.
- Repository preservation policy loaded from packaged configuration.
- Zensical navigation preservation during managed template updates.

### Changed

- Updated template handling to use the shared canonical template snapshot,
  file discovery, and rendering APIs.
- Simplified `pup-up` tests to focus on command and update behavior.
- Updated default template synchronization behavior for the current
  `pup-pack/templates` repository.

---

## [0.1.4] - 2026-08-15

### Fixed

- `pup-up` now pulls current template files.
  Downloading the template archive by branch or tag name
  returned GitHub's cached tarball, which could
  lag a recent push to `pup-pack/templates` by minutes.
  The ref is now resolved to its immutable commit SHA
  and that archive is fetched, bypassing the stale
  branch cache.

### Changed

- Template snapshots are now pinned to an exact commit:
  `TemplateSnapshot.ref` records the resolved 40-character SHA
  rather than the requested branch/tag,
  making each run reproducible and the applied template commit inspectable.
- Ref resolution adds one `api.github.com` request per run.
  `GITHUB_TOKEN` / `GH_TOKEN` are honored for a higher rate limit;
  a full SHA passed as the ref skips resolution entirely.

---

## [0.1.3] - 2026-08-13

- updated actions (one source of python version in project root)
- updated pyproject.toml
- deleted pyright; added ty and uv block in pyproject.toml
- improved fetch as a set
- zensical will keep existing nav
- starting on pyproject parts

---

## [0.1.1] - 2026-08-10

- updated the organization

---

## [0.1.0] - 2026-08-10

- transferred to pup-pack

---

## [0.0.5] - 2026-08-09

- Updated build section in pyproject.toml
- Updated docs/ and README

---

## [0.0.4] - 2026-08-08

### Changed

- Updated to use shared repository detection and core types from `pup-core`.
- Moved template-layer inference into `pup-up`.
- Moved template layers from repository context to the `pup-up` update plan.
- Updated update planning, filtering, and terminal reporting to preserve and report template layers.
- Updated tests for the new `pup-core` integration.

---

## [0.0.2] - 2026-08-08

### Added

- Updated to Python 3.15
- Refactored for maintainability
- Added optional repository-relative managed file selection.
- Added file-specific write support, such as `pup-up --write .gitattributes`.
- Added `--diff` mode to show unified diffs for existing managed files that would change.
- Added validation that selected paths are safe, repository-relative, and managed by `pup-up`.

### Changed

- Simplified the command-line interface to use a single update command without subparsers.
- Limited update plans, reports, diffs, and writes to selected managed files when paths are provided.

### Removed

- Removed the general `pup-up todo` command.
- Removed TODO report generation and the packaged `todo-surfaces.toml` configuration.
- Removed the unused TODO report type and related tests.

---

## [0.0.1] - 2026-08-04

### Added

- Initial `pup-up` command-line package.
- Added dry-run default command: `pup-up`.
- Added write mode: `pup-up --write`.
- Added repository detection from the current working directory.
- Added additive template layer inference.
- Added managed-file planning for canonical baseline files.
- Added GitHub raw template fetching from `pup-pack/templates`.
- Added optional local template source support.
- Added minimal repository identity token rendering.
- Added conservative write behavior for managed baseline files only.

---

## Notes on Versioning and Releases

- We use **SemVer**:
  - **MAJOR** - breaking changes
  - **MINOR** - backward-compatible additions
  - **PATCH** - fixes, documentation, tooling
- Versions are driven by git tags.
- Tag `vX.Y.Z` to release.
- Docs are deployed per version tag and aliased to **latest**.

## Release Procedure

Follow these steps when creating a new release.

### Task 1. Update release metadata

1. Update `CITATION.cff`: change `version` and `date-released`
2. Update `CHANGELOG.md`: move from unreleased, add entry, update links
3. Update `pyproject.toml`: update `[tool.hatch.version] fallback-version`

### Task 2. Validate

```shell
uv self update

uv python install
uv lock --upgrade
uv sync

uv run pre-commit install
uv run pre-commit autoupdate

uv run pup-up

git add -A
uv run pre-commit run --all-files
# rerun if changes made
uv run pre-commit run --all-files

uv run python -m pytest
uv run ty check
uv run python -m zensical build

uv run python -c "import shutil; from pathlib import Path; shutil.rmtree(Path('dist'), ignore_errors=True)"

uv build
uvx twine check dist/*
```

### Task 3. Commit, push, tag

```shell
git add -A
git commit -m "Prepare X.Y.Z"
git push -u origin main
```

Verify actions run on GitHub. After success:

```shell
git tag vX.Y.Z -m "X.Y.Z"
git push origin vX.Y.Z
```

## Only As Needed (delete a tag)

```shell
git tag -d vX.Z.Y
git push origin :refs/tags/vX.Z.Y
```

## Links

[Unreleased]: https://github.com/pup-pack/pup-up/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/pup-pack/pup-up/releases/tag/v0.2.0
[0.1.4]: https://github.com/pup-pack/pup-up/releases/tag/v0.1.4
[0.1.3]: https://github.com/pup-pack/pup-up/releases/tag/v0.1.3
[0.1.1]: https://github.com/pup-pack/pup-up/releases/tag/v0.1.1
[0.1.0]: https://github.com/pup-pack/pup-up/releases/tag/v0.1.0
[0.0.5]: https://github.com/pup-pack/pup-up/releases/tag/v0.0.5
[0.0.4]: https://github.com/pup-pack/pup-up/releases/tag/v0.0.4
[0.0.2]: https://github.com/pup-pack/pup-up/releases/tag/v0.0.2
[0.0.1]: https://github.com/pup-pack/pup-up/releases/tag/v0.0.1

<!-- markdownlint-enable MD024 -->
