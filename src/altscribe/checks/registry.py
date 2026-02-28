"""Checker registry — instantiates and filters active checkers."""

from __future__ import annotations

from pathlib import Path

from altscribe.checks.base import Check
from altscribe.checks.color_contrast import ColorContrastCheck
from altscribe.checks.document_language import DocumentLanguageCheck
from altscribe.checks.heading_hierarchy import HeadingHierarchyCheck
from altscribe.checks.image_alt_text import ImageAltTextCheck
from altscribe.checks.link_text import LinkTextCheck
from altscribe.checks.list_structure import ListStructureCheck
from altscribe.checks.table_accessibility import TableAccessibilityCheck

ALL_CHECK_CLASSES: list[type] = [
    ImageAltTextCheck,
    HeadingHierarchyCheck,
    LinkTextCheck,
    TableAccessibilityCheck,
    DocumentLanguageCheck,
    ListStructureCheck,
    ColorContrastCheck,
]

_NEEDS_API_KEY = {"image-alt-text", "link-text", "table-accessibility"}


def get_enabled_checks(
    *,
    api_key: str = "",
    base_dir: Path = Path("."),
    overwrite: bool = False,
    enabled: list[str] | None = None,
    disabled: list[str] | None = None,
    raw_html: str = "",
) -> list[Check]:
    """Instantiate and return the active checkers."""
    disabled = set(disabled or [])

    classes = ALL_CHECK_CLASSES
    if enabled is not None:
        enabled_set = set(enabled)
        classes = [c for c in classes if c.check_id in enabled_set]

    classes = [c for c in classes if c.check_id not in disabled]

    instances: list[Check] = []
    for cls in classes:
        cid = cls.check_id
        if cid == "image-alt-text":
            instances.append(
                cls(api_key=api_key, base_dir=base_dir, overwrite=overwrite)
            )
        elif cid == "color-contrast":
            instances.append(cls(raw_html=raw_html))
        elif cid in _NEEDS_API_KEY:
            instances.append(cls(api_key=api_key))
        else:
            instances.append(cls())

    return instances
