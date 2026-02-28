"""Color extraction from HTML — parse inline styles and CSS for color pairs."""

from __future__ import annotations

import re
from dataclasses import dataclass

# CSS named colors (most common subset).
_CSS_NAMED_COLORS: dict[str, tuple[int, int, int]] = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "silver": (192, 192, 192),
    "maroon": (128, 0, 0),
    "olive": (128, 128, 0),
    "lime": (0, 255, 0),
    "aqua": (0, 255, 255),
    "teal": (0, 128, 128),
    "navy": (0, 0, 128),
    "fuchsia": (255, 0, 255),
    "purple": (128, 0, 128),
    "orange": (255, 165, 0),
    "pink": (255, 192, 203),
    "brown": (165, 42, 42),
    "coral": (255, 127, 80),
    "crimson": (220, 20, 60),
    "darkblue": (0, 0, 139),
    "darkgreen": (0, 100, 0),
    "darkred": (139, 0, 0),
    "gold": (255, 215, 0),
    "indigo": (75, 0, 130),
    "ivory": (255, 255, 240),
    "khaki": (240, 230, 140),
    "lavender": (230, 230, 250),
    "lightblue": (173, 216, 230),
    "lightgray": (211, 211, 211),
    "lightgreen": (144, 238, 144),
    "lightyellow": (255, 255, 224),
    "tomato": (255, 99, 71),
    "turquoise": (64, 224, 208),
    "violet": (238, 130, 238),
    "wheat": (245, 222, 179),
}

_HEX3 = re.compile(r"^#([0-9a-fA-F])([0-9a-fA-F])([0-9a-fA-F])$")
_HEX6 = re.compile(r"^#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$")
_RGB = re.compile(r"^rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})")

_STYLE_COLOR = re.compile(r"(?:^|;)\s*color\s*:\s*([^;]+)", re.IGNORECASE)
_STYLE_BG = re.compile(r"(?:^|;)\s*background(?:-color)?\s*:\s*([^;]+)", re.IGNORECASE)
_INLINE_STYLE = re.compile(r'style\s*=\s*"([^"]*)"', re.IGNORECASE)
_BGCOLOR_ATTR = re.compile(r'bgcolor\s*=\s*"([^"]*)"', re.IGNORECASE)
_FONT_COLOR = re.compile(r'<font[^>]+color\s*=\s*"([^"]*)"', re.IGNORECASE)


def parse_color(color_str: str) -> tuple[int, int, int] | None:
    """Parse a CSS color value to RGB tuple.

    Supports #hex (3 or 6 digit), rgb(), rgba(), and named colors.
    """
    color_str = color_str.strip().lower()

    if color_str in _CSS_NAMED_COLORS:
        return _CSS_NAMED_COLORS[color_str]

    m = _HEX6.match(color_str)
    if m:
        return (int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16))

    m = _HEX3.match(color_str)
    if m:
        return (
            int(m.group(1) * 2, 16),
            int(m.group(2) * 2, 16),
            int(m.group(3) * 2, 16),
        )

    m = _RGB.match(color_str)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))

    return None


@dataclass
class ColorPair:
    """A foreground/background color pair found in a document."""

    foreground: tuple[int, int, int]
    background: tuple[int, int, int]
    location: str
    is_large_text: bool = False


def extract_color_pairs(html: str) -> list[ColorPair]:
    """Extract foreground/background color pairs from HTML source.

    Looks for inline style attributes and legacy HTML color attributes.
    Assumes white background when only foreground is specified.
    """
    pairs: list[ColorPair] = []
    default_bg = (255, 255, 255)

    # Extract from inline styles
    for i, m in enumerate(_INLINE_STYLE.finditer(html)):
        style = m.group(1)
        fg_match = _STYLE_COLOR.search(style)
        bg_match = _STYLE_BG.search(style)

        fg = parse_color(fg_match.group(1)) if fg_match else None
        bg = parse_color(bg_match.group(1)) if bg_match else None

        if fg:
            pairs.append(
                ColorPair(
                    foreground=fg,
                    background=bg or default_bg,
                    location=f"inline style #{i + 1}",
                )
            )

    # Extract from bgcolor attributes
    for i, m in enumerate(_BGCOLOR_ATTR.finditer(html)):
        bg = parse_color(m.group(1))
        if bg:
            pairs.append(
                ColorPair(
                    foreground=(0, 0, 0),
                    background=bg,
                    location=f"bgcolor #{i + 1}",
                )
            )

    # Extract from <font color="..."> tags
    for i, m in enumerate(_FONT_COLOR.finditer(html)):
        fg = parse_color(m.group(1))
        if fg:
            pairs.append(
                ColorPair(
                    foreground=fg,
                    background=default_bg,
                    location=f"font color #{i + 1}",
                )
            )

    return pairs
