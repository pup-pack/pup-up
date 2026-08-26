"""Apply or preview the managed repository baseline."""

from collections.abc import Sequence
from pathlib import Path

from pup_core.inspect.detect import detect_repository
from pup_core.templates.baseline import infer_layers
from pup_core.templates.fetch import TemplateSource, fetch_template_snapshot

from pup_up.sync.plan import (
    build_update_plan,
    filter_update_plan,
    write_update_plan,
)
from pup_up.write.terminal import (
    print_update_diffs,
    print_update_plan,
)

__all__ = ["run"]


def run(
    *,
    root: Path | None = None,
    write: bool = False,
    show_diff: bool = False,
    selected_paths: Sequence[Path] = (),
    templates: str = "pup-pack/templates",
    ref: str = "main",
    templates_path: Path | None = None,
) -> int:
    """Preview or apply managed baseline updates.

    Args:
        root: Repository root. If None, pup-up detects the current repo root.
        write: Whether to write changes. False means dry-run only.
        show_diff: Whether to print unified diffs for changed managed files.
        selected_paths: Optional repository-relative managed files to process.
        templates: GitHub owner/repo for canonical templates.
        ref: Git ref, branch, or tag.
        templates_path: Optional local templates repo path.

    Returns:
        Process exit code.
    """
    repository = detect_repository(root)
    layers = tuple(
        infer_layers(
            repo_root=repository.root,
            repo_name=repository.repo_name,
            files=set(repository.files),
        )
    )
    source = TemplateSource(
        repository=templates,
        ref=ref,
        local_path=templates_path,
    )

    with fetch_template_snapshot(source=source) as snapshot:
        plan = build_update_plan(
            target=repository,
            layers=layers,
            snapshot=snapshot,
            protected_paths=frozenset({"docs/api.md", "README.md"}),
        )

    if selected_paths:
        plan = filter_update_plan(plan, selected_paths)

    print_update_plan(plan, write=write)

    if show_diff:
        print_update_diffs(plan)

    if write:
        write_update_plan(plan)

    return 0
