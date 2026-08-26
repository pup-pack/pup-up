"""Print update plans."""

from difflib import unified_diff

from pup_up.base.types import FileStatus, UpdatePlan

__all__ = [
    "print_update_diffs",
    "print_update_plan",
]


def print_update_plan(plan: UpdatePlan, *, write: bool) -> None:
    """Print a human-readable update plan.

    Args:
        plan: Update plan to print.
        write: Whether the plan is being applied (True) or is a dry run (False).

    Returns:
        None.
    """
    mode = "WRITE" if write else "DRY RUN"

    print(f"[pup-up] {mode}")
    print(f"[pup-up] repo: {plan.target.repo_name}")
    print(f"[pup-up] root: {plan.target.root}")
    print(f"[pup-up] layers: {' -> '.join(plan.layers)}")
    print(" ")

    counts = _status_counts(plan)

    print("[pup-up] managed files")
    for file in plan.files:
        status = _status_label(file.status, write=write)
        source_label = f" [{file.source_layer}]" if file.source_layer else ""
        print(f"{status:13} {file.path.as_posix()}{source_label}")

    print(" ")
    print(
        "[pup-up] summary: "
        f"{counts['current']} current, "
        f"{counts['changed']} changed, "
        f"{counts['missing']} missing, "
        f"{counts['no-template']} no-template, "
        f"{counts['protected']} protected"
    )

    if not write:
        print(" ")
        print(
            "[pup-up] no files written; rerun with --diff to see changes, or with --write to apply changes"
        )


def print_update_diffs(plan: UpdatePlan) -> None:
    """Print unified diffs for changed managed files.

    Args:
        plan: Update plan containing the files to diff.

    Returns:
        None.
    """
    for file in plan.files:
        if file.status != "changed":
            continue

        if file.current_text is None or file.desired_text is None:
            continue

        relative_path = file.path.as_posix()

        diff_lines = unified_diff(
            file.current_text.splitlines(keepends=True),
            file.desired_text.splitlines(keepends=True),
            fromfile=f"current/{relative_path}",
            tofile=f"canonical/{relative_path}",
        )

        print(" ")
        print(f"[pup-up] diff: {relative_path}")

        for line in diff_lines:
            print(line, end="")


def _status_counts(plan: UpdatePlan) -> dict[FileStatus, int]:
    """Count file statuses."""
    counts: dict[FileStatus, int] = {
        "current": 0,
        "changed": 0,
        "missing": 0,
        "no-template": 0,
        "protected": 0,
    }

    for file in plan.files:
        counts[file.status] += 1

    return counts


def _status_label(status: FileStatus, *, write: bool) -> str:
    """Return display label for a file status."""
    match status:
        case "current":
            return "CURRENT"
        case "changed":
            return "CHANGED" if write else "WOULD CHANGE"
        case "missing":
            return "ADDED" if write else "WOULD ADD"
        case "no-template":
            return "NO TEMPLATE"
        case "protected":
            return "PROTECTED"
