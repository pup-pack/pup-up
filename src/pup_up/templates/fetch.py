"""Template source access."""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import io
import os
from pathlib import Path
import re
import tarfile
from tempfile import TemporaryDirectory
import tomllib
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from pup_up.base.errors import TemplateFetchError

# Matches a full Git commit SHA-1:
# exactly 40 lowercase hexadecimal digits.
#
#   ^          anchor at the start of the string
#   [0-9a-f]   one hex digit: digits 0-9 and lowercase a-f ONLY
#              (uppercase is intentionally rejected; GitHub emits lowercase,
#               and rejecting mixed case keeps "is this already a SHA?"
#               unambiguous)
#   {40}       exactly 40 of them: a full SHA-1, never an abbreviated one
#              (a 7-char short SHA will NOT match, so it gets sent through
#               ref resolution like any branch name:
#               short SHAs are not valid in the codeload archive URL)
#   $          anchor at the end
#
# Used to decide whether `ref` is ALREADY an immutable commit
# (skip the API resolution) or a branch/tag name (resolve it to a SHA first).
# Anything not a full lowercase 40-hex string, e.g.:
# "main", "v1.2.3", a short SHA: is treated as a name to resolve.
#
# NOTE: `$` matches at end-of-string OR just before a trailing "\n",
# so a value with a trailing newline would match.
# Fine here because every value tested is either
# `source.ref` or the `.strip()`-ed API response.
# Use `\Z` instead of `$` if the trailing newline must be forbidden.
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

__all__ = [
    "TemplateFile",
    "TemplateSnapshot",
    "TemplateSource",
    "fetch_template_snapshot",
    "fetch_template_text",
    "list_template_files",
    "load_preserve_patterns",
]


@dataclass(frozen=True)
class TemplateFile:
    """Describe one managed file discovered in a template layer.

    Attributes:
        layer: Template layer that supplies the effective file.
        template_path: Path to the source file relative to the template layer.
        target_path: Repository-relative path where the file applies.
    """

    layer: str
    template_path: str
    target_path: str


@dataclass(frozen=True)
class TemplateSnapshot:
    """Describe one resolved local snapshot of the template repository.

    A snapshot provides a stable local source for all template operations
    performed during a run. Remote sources are resolved to an immutable commit
    before being downloaded.

    Attributes:
        root: Local root directory containing the resolved template tree.
        repository: GitHub owner/repository identifying the template source.
        ref: Resolved Git reference. Remote snapshots use the immutable commit SHA.
        from_local: Whether the snapshot came from an explicitly supplied local path.
    """

    root: Path
    repository: str
    ref: str
    from_local: bool


@dataclass(frozen=True)
class TemplateSource:
    """Describe the canonical source from which templates should be resolved.

    Attributes:
        repository: GitHub owner/repository containing the templates.
        ref: Git branch, tag, or commit to resolve.
        local_path: Optional local template repository path that bypasses downloading.
    """

    repository: str = "pup-pack/templates"
    ref: str = "main"
    local_path: Path | None = None


@contextmanager
def fetch_template_snapshot(*, source: TemplateSource) -> Iterator[TemplateSnapshot]:
    """Resolve a template source to one stable local snapshot.

    A local source is used directly. A remote source is first resolved to an
    immutable commit SHA, downloaded as a GitHub archive, and extracted into a
    temporary directory that remains available for the duration of the context.

    Args:
        source: Template repository, Git reference, and optional local path.

    Yields:
        Resolved local template snapshot.

    Raises:
        TemplateFetchError: If a remote reference cannot be resolved, the archive
            cannot be downloaded or extracted, or the extracted snapshot has an
            invalid directory structure.
    """
    if source.local_path is not None:
        yield TemplateSnapshot(
            root=source.local_path.expanduser().resolve(),
            repository=source.repository,
            ref=source.ref,
            from_local=True,
        )
        return

    with TemporaryDirectory(prefix="pup-up-templates-") as raw_dest:
        root, commit = _download_and_extract_snapshot(
            repository=source.repository,
            ref=source.ref,
            dest=Path(raw_dest),
        )
        yield TemplateSnapshot(
            root=root,
            repository=source.repository,
            ref=commit,
            from_local=False,
        )


def fetch_template_text(
    *,
    snapshot: TemplateSnapshot,
    template_file: TemplateFile,
) -> str | None:
    """Read one UTF-8 template file from a resolved snapshot.

    Args:
        snapshot: Resolved local template snapshot.
        template_file: Effective template file to read.

    Returns:
        Template text, or None if the referenced path does not exist or is not
        a regular file.

    Raises:
        TemplateFetchError: If the template file exists but cannot be read.
    """
    path = snapshot.root / template_file.layer / template_file.template_path

    if not path.exists() or path.is_dir():
        return None

    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise TemplateFetchError(f"Could not read template file: {path}") from exc


def list_template_files(
    *,
    snapshot: TemplateSnapshot,
    layers: list[str],
) -> list[TemplateFile]:
    """Return the effective managed files supplied by selected template layers.

    Layers are processed in order. When multiple layers provide the same target
    path, the later and more specific layer supersedes the earlier one.

    Args:
        snapshot: Resolved local template snapshot.
        layers: Ordered template layers to inspect.

    Returns:
        Effective managed template files after layer overrides are applied.
    """
    discovered = _list_template_files(root=snapshot.root, layers=layers)

    by_target: dict[str, TemplateFile] = {}
    for item in discovered:
        by_target[item.target_path] = item

    return list(by_target.values())


def load_preserve_patterns(*, snapshot: TemplateSnapshot) -> tuple[str, ...]:
    """Load repository-preservation patterns from template policy.

    Args:
        snapshot: Resolved local template snapshot containing policy.toml.

    Returns:
        Repository-relative glob patterns identifying surfaces that should be
        preserved. Returns an empty tuple when policy.toml is absent.

    Raises:
        TemplateFetchError: If policy.toml cannot be read or parsed, or if
            preserve_patterns is not an array containing only strings.
    """
    path = snapshot.root / "policy.toml"

    if not path.is_file():
        return ()

    try:
        with path.open("rb") as file:
            data = tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise TemplateFetchError(
            f"Could not read template configuration: {path}"
        ) from exc

    patterns = data.get("preserve_patterns", [])

    if not isinstance(patterns, list):
        raise TemplateFetchError(f"preserve_patterns must be a TOML array: {path}")

    if not all(isinstance(pattern, str) for pattern in patterns):
        raise TemplateFetchError(f"preserve_patterns must contain only strings: {path}")

    return tuple(patterns)


def _download_and_extract_snapshot(
    *,
    repository: str,
    ref: str,
    dest: Path,
) -> tuple[Path, str]:
    """Resolve, download, and extract one immutable template snapshot.

    Args:
        repository: GitHub owner/repository containing the templates.
        ref: Branch, tag, or commit identifying the requested snapshot.
        dest: Directory into which the archive should be extracted.

    Returns:
        Tuple containing the extracted snapshot root and resolved commit SHA.

    Raises:
        TemplateFetchError: If the reference cannot be resolved, the archive
            cannot be downloaded or extracted, or the resulting archive layout
            is invalid.
    """
    commit = _resolve_ref_to_commit(repository=repository, ref=ref)
    url = f"https://codeload.github.com/{repository}/tar.gz/{commit}"

    archive_bytes = _fetch_archive_bytes(url)

    try:
        with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as archive:
            archive.extractall(path=dest, filter="data")
    except (tarfile.TarError, OSError) as exc:
        raise TemplateFetchError(f"Could not extract template snapshot: {url}") from exc

    return _snapshot_root(dest=dest, url=url), commit


def _fetch_archive_bytes(url: str) -> bytes:
    """Download a template archive from the trusted GitHub archive host.

    Args:
        url: HTTPS codeload.github.com archive URL.

    Returns:
        Downloaded archive bytes.

    Raises:
        TemplateFetchError: If the URL is not HTTPS, does not use the trusted
            GitHub archive host, or cannot be downloaded.
    """
    parsed = urlparse(url)

    if parsed.scheme != "https":
        raise TemplateFetchError(f"Invalid URL scheme: {url}")

    if parsed.netloc != "codeload.github.com":
        raise TemplateFetchError(f"Invalid template host: {url}")

    request = Request(
        url,
        headers={
            "User-Agent": "pup-up",
        },
    )

    try:
        with urlopen(request, timeout=60) as response:
            return response.read()
    except HTTPError as exc:
        raise TemplateFetchError(
            f"Could not download template snapshot: {url}"
        ) from exc
    except URLError as exc:
        raise TemplateFetchError(
            f"Could not download template snapshot: {url}"
        ) from exc


def _list_template_files(
    *,
    root: Path,
    layers: list[str],
) -> list[TemplateFile]:
    """Discover template files from ordered layers in a local template tree.

    Args:
        root: Local template repository root.
        layers: Ordered template layers to inspect.

    Returns:
        Discovered template files before target-path overrides are resolved.
    """
    resolved_root = root.expanduser().resolve()
    items: list[TemplateFile] = []

    for layer in layers:
        layer_root = resolved_root / layer
        if not layer_root.exists():
            continue

        for template_path in sorted(layer_root.rglob("*")):
            if not template_path.is_file():
                continue

            relative_path = template_path.relative_to(layer_root).as_posix()
            if _should_skip_template_path(relative_path):
                continue

            items.append(
                TemplateFile(
                    layer=layer,
                    template_path=relative_path,
                    target_path=_target_path_for_template_path(relative_path),
                )
            )

    return items


def _resolve_ref_to_commit(*, repository: str, ref: str) -> str:
    """Resolve a GitHub branch or tag to an immutable full commit SHA.

    A full 40-character lowercase SHA is returned unchanged. Other references
    are resolved through the GitHub commits API.

    Args:
        repository: GitHub owner/repository containing the templates.
        ref: Branch, tag, or full commit SHA.

    Returns:
        Full lowercase 40-character commit SHA.

    Raises:
        TemplateFetchError: If the reference cannot be resolved or GitHub
            returns an invalid commit SHA.
    """
    if _SHA_RE.match(ref):
        return ref

    api_url = (
        f"https://api.github.com/repos/{repository}/commits/{quote(ref, safe='/')}"
    )
    headers = {
        "User-Agent": "pup-up",
        "Accept": "application/vnd.github.sha",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(api_url, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            sha = response.read().decode("utf-8").strip()
    except HTTPError as exc:
        raise TemplateFetchError(f"Could not resolve template ref: {api_url}") from exc
    except URLError as exc:
        raise TemplateFetchError(f"Could not resolve template ref: {api_url}") from exc

    if not _SHA_RE.match(sha):
        raise TemplateFetchError(f"Unexpected ref resolution for {api_url}: {sha!r}")

    return sha


def _should_skip_template_path(path: str) -> bool:
    """Return whether a template path is internal or unsupported."""
    if not path:
        return True

    if path.startswith((".pup-up/", "__pycache__/")):
        return True

    if Path(path).name == ".DS_Store":
        return True

    return path.endswith(".pyc")


def _snapshot_root(*, dest: Path, url: str) -> Path:
    """Return the single root directory extracted from a GitHub archive.

    Args:
        dest: Directory containing the extracted archive.
        url: Source archive URL used for diagnostic messages.

    Returns:
        Single extracted top-level directory.

    Raises:
        TemplateFetchError: If extraction does not produce exactly one
            top-level directory.
    """
    directories = [entry for entry in dest.iterdir() if entry.is_dir()]

    if len(directories) != 1:
        raise TemplateFetchError(f"Unexpected template snapshot layout: {url}")

    return directories[0]


def _target_path_for_template_path(path: str) -> str:
    """Convert a template path to a target repository path."""
    if path.endswith(".template"):
        return path.removesuffix(".template")

    return path
