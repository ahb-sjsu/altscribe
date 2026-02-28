"""WCAG 2.1 color contrast computation — pure Python, no dependencies."""

from __future__ import annotations

from dataclasses import dataclass


def _linearize(c: int) -> float:
    """Convert sRGB channel (0-255) to linear RGB."""
    s = c / 255.0
    return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: tuple[int, int, int]) -> float:
    """Compute relative luminance per WCAG 2.1 definition.

    See https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
    """
    r, g, b = rgb
    return 0.2126 * _linearize(r) + 0.7152 * _linearize(g) + 0.0722 * _linearize(b)


def contrast_ratio(color1: tuple[int, int, int], color2: tuple[int, int, int]) -> float:
    """Compute WCAG contrast ratio between two sRGB colors.

    Returns a value between 1.0 (identical) and 21.0 (black on white).
    """
    l1 = relative_luminance(color1)
    l2 = relative_luminance(color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


@dataclass
class ContrastResult:
    """Result of a WCAG contrast check between two colors."""

    foreground: tuple[int, int, int]
    background: tuple[int, int, int]
    ratio: float
    aa_normal: bool  # >= 4.5:1
    aa_large: bool  # >= 3:1
    aaa_normal: bool  # >= 7:1
    aaa_large: bool  # >= 4.5:1


def check_contrast(
    fg: tuple[int, int, int], bg: tuple[int, int, int]
) -> ContrastResult:
    """Check a foreground/background pair against all WCAG thresholds."""
    ratio = round(contrast_ratio(fg, bg), 2)
    return ContrastResult(
        foreground=fg,
        background=bg,
        ratio=ratio,
        aa_normal=ratio >= 4.5,
        aa_large=ratio >= 3.0,
        aaa_normal=ratio >= 7.0,
        aaa_large=ratio >= 4.5,
    )
