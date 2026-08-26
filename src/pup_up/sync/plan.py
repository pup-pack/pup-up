"""Build and apply update plans."""

from collections.abc import Sequence
from pathlib import Path

from pup_core.base.types import RepositoryContext
from pup_core.templates.baseline import list_template_files
from pup_core.templates.render import read_rendered_template
from pup_core.templates.types import TemplateFile, TemplateSnapshot

from pup_up.base.errors import PupUpError, UnsafePathError
from pup_up.base.types import FileStatus, PlannedFile, UpdatePlan
from pup_up.templates.zensical import preserve_zensical_navigation

__all__ = [
    "FileReadError",
    "FileWriteError",
    "build_update_plan",
    "filter_update_plan",
    "write_update_plan",
]


class FileReadError(PupUpError):
    """Raised when a managed file cannot be read."""


class FileWriteError(PupUpError):
    """Raised when a managed file cannot be written."""


def build_update_plan(
    *,
    target: RepositoryContext,
    layers: tuple[str, ...],
    snapshot: TemplateSnapshot,
    protected_paths: frozenset[str] = frozenset(),
) -> UpdatePlan:
    """Build an update plan from discovered template files.

    Args:
        target: Detected context for the target repository.
        layers: Ordered tuple of template layers to consider.
        snapshot: Resolved canonical template snapshot.
        protected_paths: Repository-relative paths that must not be modified.

    Returns:
        Update plan representing the proposed changes.

    Raises:
        FileReadError: If a managed repository file cannot be read.
        UnsafePathError: If a managed file resolves outside the repository root.
    """
    planned_files: list[PlannedFile] = []

    template_files = list_template_files(
        snapshot=snapshot,
        layers=list(layers),
    )

    for template_file in template_files:
        planned_files.append(
            _plan_one_template_file(
                target=target,
                snapshot=snapshot,
                template_file=template_file,
                protected_paths=protected_paths,
            )
        )

    return UpdatePlan(
        target=target,
        layers=layers,
        files=tuple(planned_files),
    )


def filter_update_plan(
    plan: UpdatePlan,
    selected_paths: Sequence[Path],
) -> UpdatePlan:
    """Return an update plan containing only selected managed files.

    Args:
        plan: Complete update plan.
        selected_paths: Repository-relative managed file paths to retain.

    Returns:
        Filtered update plan.

    Raises:
        ValueError: If a selected path is absolute, escapes the repository,
            or is not included in the managed update plan.
    """
    normalized_selected: set[str] = set()

    for path in selected_paths:
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(
                f"Selected path must be repository-relative and safe: {path}"
            )

        normalized_selected.add(path.as_posix())

    managed_paths = {file.path.as_posix() for file in plan.files}
    unknown_paths = normalized_selected - managed_paths

    if unknown_paths:
        paths = ", ".join(sorted(unknown_paths))
        raise ValueError(f"Selected path is not managed by pup-up: {paths}")

    filtered_files = tuple(
        file for file in plan.files if file.path.as_posix() in normalized_selected
    )

    return UpdatePlan(
        target=plan.target,
        layers=plan.layers,
        files=filtered_files,
    )


def write_update_plan(plan: UpdatePlan) -> None:
    """Write changed or missing managed files.

    Args:
        plan: Update plan containing the managed files to write.

    Raises:
        FileWriteError: If a managed file cannot be created or written.
        UnsafePathError: If a managed file resolves outside the repository root.
    """
    for file in plan.files:
        if file.status not in {"changed", "missing"}:
            continue

        if file.desired_text is None:
            continue

        target_path = _safe_target_path(plan.target.root, file.path)

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(file.desired_text, encoding="utf-8")
        except OSError as exc:
            raise FileWriteError(
                f"Could not write managed file: {target_path}"
            ) from exc


def _plan_one_template_file(
    *,
    target: RepositoryContext,
    snapshot: TemplateSnapshot,
    template_file: TemplateFile,
    protected_paths: frozenset[str],
) -> PlannedFile:
    """Plan one discovered template file.

    Args:
        target: Detected context for the target repository.
        snapshot: Resolved canonical template snapshot.
        template_file: Effective template file to plan.
        protected_paths: Repository-relative paths that must not be modified.

    Returns:
        Planned file state for the effective template file.

    Raises:
        FileReadError: If the current managed file cannot be read.
        UnsafePathError: If the managed file resolves outside the repository root.
    """
    desired_text = read_rendered_template(
        snapshot=snapshot,
        template_file=template_file,
        repository=target,
    )

    relative_path = Path(template_file.target_path)
    current_text = _read_current_text(target.root, relative_path)

    if relative_path.as_posix() in protected_paths:
        return PlannedFile(
            path=relative_path,
            status="protected",
            source_layer=template_file.layer,
            source_path=f"{template_file.layer}/{template_file.template_path}",
            current_text=current_text,
            desired_text=desired_text,
        )

    if relative_path == Path("zensical.toml") and current_text is not None:
        desired_text = preserve_zensical_navigation(
            existing_text=current_text,
            rendered_text=desired_text,
        )

    status = _file_status(
        current_text=current_text,
        desired_text=desired_text,
    )

    return PlannedFile(
        path=relative_path,
        status=status,
        source_layer=template_file.layer,
        source_path=f"{template_file.layer}/{template_file.template_path}",
        current_text=current_text,
        desired_text=desired_text,
    )


def _file_status(
    *,
    current_text: str | None,
    desired_text: str,
) -> FileStatus:
    """Determine planned file status."""
    if current_text is None:
        return "missing"

    if current_text == desired_text:
        return "current"

    return "changed"


def _read_current_text(root: Path, path: Path) -> str | None:
    """Read current managed file text if present.

    Args:
        root: Repository root.
        path: Repository-relative managed file path.

    Returns:
        UTF-8 file text, or None if the path does not exist, is a directory,
        or contains non-UTF-8 content.

    Raises:
        FileReadError: If the file exists but cannot otherwise be read.
        UnsafePathError: If the path resolves outside the repository root.
    """
    target_path = _safe_target_path(root, path)

    if not target_path.exists() or target_path.is_dir():
        return None

    try:
        return target_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    except OSError as exc:
        raise FileReadError(f"Could not read managed file: {target_path}") from exc


def _safe_target_path(root: Path, path: Path) -> Path:
    """Resolve a path safely under the repository root.

    Args:
        root: Repository root.
        path: Repository-relative path to resolve.

    Returns:
        Resolved path beneath the repository root.

    Raises:
        UnsafePathError: If the resolved path escapes the repository root.
    """
    target_path = (root / path).resolve()
    root_resolved = root.resolve()

    if target_path != root_resolved and root_resolved not in target_path.parents:
        raise UnsafePathError(target_path)

    return target_path
