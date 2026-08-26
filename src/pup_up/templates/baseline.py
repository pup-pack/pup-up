"""Baseline layer inference and managed file declarations."""

from pathlib import Path
import tomllib

__all__ = ["infer_layers", "load_preserve_patterns"]


def load_preserve_patterns() -> tuple[str, ...]:
    """Load repository preserve patterns from pup-up policy data."""
    data_path = Path(__file__).parent / "data" / "policy.toml"

    with data_path.open("rb") as file:
        data = tomllib.load(file)

    patterns = data.get("preserve_patterns", [])

    if not isinstance(patterns, list) or not all(
        isinstance(pattern, str) for pattern in patterns
    ):
        raise ValueError(f"Invalid preserve_patterns in {data_path}")

    return tuple(patterns)


def infer_layers(*, repo_root: Path, repo_name: str, files: set[str]) -> list[str]:
    """Infer additive template layers based strictly on file existence."""
    # 1. Identify physical markers
    has_py = "pyproject.toml" in files
    has_src = (repo_root / "src").is_dir()
    is_ts = "package.json" in files

    # 2. Build Layers (Ordered by specificity)
    layers: list[str] = ["ALL"]

    # Base Tooling
    if has_py:
        layers.append("ALL-PY")
    elif is_ts:
        layers.append("ALL-TS")

    # Structural Overlays
    if has_py and has_src:
        layers.append("ALL-PY-SRC")

    return layers
