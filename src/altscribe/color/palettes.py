"""ColorBrewer2 palette data and accessible palette suggestion engine."""

from __future__ import annotations

from dataclasses import dataclass

from altscribe.color.colorblind import CVDType, colors_distinguishable
from altscribe.color.contrast import contrast_ratio

# Subset of ColorBrewer2 qualitative palettes (public domain).
# Source: https://colorbrewer2.org/ by Cynthia Brewer.
COLORBREWER_QUALITATIVE: dict[str, list[tuple[int, int, int]]] = {
    "Set2": [
        (102, 194, 165),
        (252, 141, 98),
        (141, 160, 203),
        (231, 138, 195),
        (166, 216, 84),
        (255, 217, 47),
        (229, 196, 148),
        (179, 179, 179),
    ],
    "Dark2": [
        (27, 158, 119),
        (217, 95, 2),
        (117, 112, 179),
        (231, 41, 138),
        (102, 166, 30),
        (230, 171, 2),
        (166, 118, 29),
        (102, 102, 102),
    ],
    "Paired": [
        (166, 206, 227),
        (31, 120, 180),
        (178, 223, 138),
        (51, 160, 44),
        (251, 154, 153),
        (227, 26, 28),
        (253, 191, 111),
        (255, 127, 0),
    ],
    "Set1": [
        (228, 26, 28),
        (55, 126, 184),
        (77, 175, 74),
        (152, 78, 163),
        (255, 127, 0),
        (255, 255, 51),
        (166, 86, 40),
        (247, 129, 191),
    ],
    "Accent": [
        (127, 201, 127),
        (190, 174, 212),
        (253, 192, 134),
        (255, 255, 153),
        (56, 108, 176),
        (240, 2, 127),
        (191, 91, 23),
        (102, 102, 102),
    ],
}

# Okabe-Ito palette — widely recommended for color blindness accessibility.
OKABE_ITO: list[tuple[int, int, int]] = [
    (0, 114, 178),  # blue
    (230, 159, 0),  # orange
    (0, 158, 115),  # green
    (204, 121, 167),  # pink
    (86, 180, 233),  # sky blue
    (213, 94, 0),  # vermillion
    (240, 228, 66),  # yellow
    (0, 0, 0),  # black
]


@dataclass
class PaletteSuggestion:
    """A palette that meets the requested accessibility constraints."""

    name: str
    colors: list[tuple[int, int, int]]
    min_contrast: float
    cvd_safe: bool


def _check_palette_contrast(
    colors: list[tuple[int, int, int]],
    background: tuple[int, int, int],
) -> float:
    """Return the minimum contrast ratio of any color against the background."""
    if not colors:
        return 0.0
    return min(contrast_ratio(c, background) for c in colors)


def _check_palette_cvd(colors: list[tuple[int, int, int]]) -> bool:
    """Check if all color pairs in the palette are distinguishable under CVD."""
    for cvd_type in CVDType:
        for i, c1 in enumerate(colors):
            for c2 in colors[i + 1 :]:
                if not colors_distinguishable(c1, c2, cvd_type):
                    return False
    return True


def suggest_accessible_palette(
    num_colors: int,
    background: tuple[int, int, int] = (255, 255, 255),
    min_contrast: float = 4.5,
    cvd_safe: bool = True,
) -> list[PaletteSuggestion]:
    """Suggest palettes that meet contrast and CVD requirements.

    Parameters
    ----------
    num_colors : How many distinct colors are needed.
    background : Background color to check contrast against.
    min_contrast : Minimum contrast ratio against background.
    cvd_safe : If True, only include palettes where all pairs
               are distinguishable under all CVD types.

    Returns
    -------
    List of PaletteSuggestion, sorted by min_contrast descending.
    """
    candidates: dict[str, list[tuple[int, int, int]]] = {
        **COLORBREWER_QUALITATIVE,
        "Okabe-Ito": OKABE_ITO,
    }

    suggestions: list[PaletteSuggestion] = []
    for name, full_palette in candidates.items():
        if len(full_palette) < num_colors:
            continue
        subset = full_palette[:num_colors]
        mc = _check_palette_contrast(subset, background)
        is_cvd_safe = _check_palette_cvd(subset)

        if mc >= min_contrast and (not cvd_safe or is_cvd_safe):
            suggestions.append(
                PaletteSuggestion(
                    name=name,
                    colors=subset,
                    min_contrast=round(mc, 2),
                    cvd_safe=is_cvd_safe,
                )
            )

    suggestions.sort(key=lambda s: s.min_contrast, reverse=True)
    return suggestions


def suggest_replacement(
    failing_fg: tuple[int, int, int],
    bg: tuple[int, int, int],
    min_contrast: float = 4.5,
) -> tuple[int, int, int]:
    """Find an accessible color close to failing_fg by adjusting lightness.

    Darkens or lightens the foreground color until contrast meets threshold.
    """
    r, g, b = failing_fg
    current_ratio = contrast_ratio(failing_fg, bg)

    if current_ratio >= min_contrast:
        return failing_fg

    bg_luminance = (
        0.2126 * (bg[0] / 255) + 0.7152 * (bg[1] / 255) + 0.0722 * (bg[2] / 255)
    )
    should_darken = bg_luminance > 0.5

    best = failing_fg
    for step in range(1, 256):
        if should_darken:
            candidate = (max(0, r - step), max(0, g - step), max(0, b - step))
        else:
            candidate = (min(255, r + step), min(255, g + step), min(255, b + step))

        ratio = contrast_ratio(candidate, bg)
        if ratio >= min_contrast:
            return candidate
        best = candidate

    return best
