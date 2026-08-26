"""Zensical-specific template update helpers.

Logic:

if existing project file has nav
    existing nav always wins

if existing project file has no nav
    use rendered template
"""

import re

# RE matches:
# nav = [
# nav=[
# nav= [
# nav   =   [
#     nav = [
NAV_PATTERN = re.compile(r"(?m)^[ \t]*nav[ \t]*=[ \t]*\[")


def preserve_zensical_navigation(
    existing_text: str,
    rendered_text: str,
) -> str:
    """Preserve existing Zensical navigation when present.

    Args:
        existing_text: Current content of the project file.
        rendered_text: Newly rendered template content.

    Returns:
        Combined template content with existing navigation preserved when present.
    """
    existing_match = NAV_PATTERN.search(existing_text)

    # No existing navigation: use the rendered template exactly as-is.
    if existing_match is None:
        return rendered_text

    # Existing navigation is repository-owned and extends through EOF.
    existing_nav = existing_text[existing_match.start() :]

    return rendered_text.rstrip() + "\n\n" + existing_nav
