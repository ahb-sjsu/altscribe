"""Color contrast checker — WCAG SC 1.4.3, 1.4.11."""

from __future__ import annotations

import panflute as pf

from altscribe.checks.base import BaseCheck, CheckResult, Severity
from altscribe.color.colorblind import CVDType, colors_distinguishable
from altscribe.color.contrast import check_contrast
from altscribe.color.extraction import ColorPair, extract_color_pairs
from altscribe.color.palettes import suggest_replacement


def _rgb_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


class ColorContrastCheck(BaseCheck):
    check_id = "color-contrast"
    check_name = "Color Contrast"
    wcag_sc = "1.4.3"
    element_types = (pf.Doc,)

    def __init__(self, raw_html: str = "") -> None:
        super().__init__()
        self._raw_html = raw_html
        self._color_pairs: list[ColorPair] = []

    def check(self, elem: pf.Element, doc: pf.Doc) -> None:
        if not self._raw_html:
            return

        self._color_pairs = extract_color_pairs(self._raw_html)

        for pair in self._color_pairs:
            result = check_contrast(pair.foreground, pair.background)
            required = 3.0 if pair.is_large_text else 4.5

            if result.ratio < required:
                self._add_issue(
                    message=(
                        f"Insufficient contrast ratio {result.ratio}:1 "
                        f"(requires {required}:1) for "
                        f"fg={_rgb_hex(pair.foreground)} on "
                        f"bg={_rgb_hex(pair.background)}"
                    ),
                    location=pair.location,
                )

            # CVD distinguishability warnings
            for cvd_type in CVDType:
                if not colors_distinguishable(
                    pair.foreground, pair.background, cvd_type
                ):
                    self._add_issue(
                        message=(
                            f"Colors indistinguishable under {cvd_type.value}: "
                            f"fg={_rgb_hex(pair.foreground)} "
                            f"bg={_rgb_hex(pair.background)}"
                        ),
                        location=pair.location,
                        severity=Severity.WARNING,
                    )

    def finalize(self, doc: pf.Doc, fix: bool) -> CheckResult:
        if fix and self._raw_html:
            for issue in self._issues:
                if issue.severity == Severity.ERROR and not issue.fixed:
                    # Find the corresponding color pair and suggest fix
                    for pair in self._color_pairs:
                        result = check_contrast(pair.foreground, pair.background)
                        required = 3.0 if pair.is_large_text else 4.5
                        if result.ratio < required and issue.location == pair.location:
                            new_fg = suggest_replacement(
                                pair.foreground, pair.background, required
                            )
                            issue.fixed = True
                            new_ratio = check_contrast(new_fg, pair.background).ratio
                            issue.fix_description = (
                                f"Suggested: change fg to "
                                f"{_rgb_hex(new_fg)} "
                                f"(contrast {new_ratio}:1)"
                            )
                            break

        return self._make_result()
