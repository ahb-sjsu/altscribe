"""Tests for ColorBrewer palette suggestions."""

from altscribe.color.palettes import (
    COLORBREWER_QUALITATIVE,
    OKABE_ITO,
    suggest_accessible_palette,
    suggest_replacement,
)


class TestPaletteData:
    def test_colorbrewer_palettes_not_empty(self):
        assert len(COLORBREWER_QUALITATIVE) > 0
        for name, colors in COLORBREWER_QUALITATIVE.items():
            assert len(colors) >= 3, f"{name} has too few colors"

    def test_okabe_ito_has_eight_colors(self):
        assert len(OKABE_ITO) == 8

    def test_all_colors_valid_rgb(self):
        for colors in COLORBREWER_QUALITATIVE.values():
            for r, g, b in colors:
                assert 0 <= r <= 255
                assert 0 <= g <= 255
                assert 0 <= b <= 255


class TestSuggestAccessiblePalette:
    def test_returns_suggestions(self):
        results = suggest_accessible_palette(3, cvd_safe=False, min_contrast=1.0)
        assert len(results) > 0

    def test_respects_min_contrast(self):
        results = suggest_accessible_palette(
            3, background=(255, 255, 255), min_contrast=4.5, cvd_safe=False
        )
        for s in results:
            assert s.min_contrast >= 4.5

    def test_empty_for_impossible_requirements(self):
        # 21:1 minimum contrast with 8 colors — unlikely to find anything
        results = suggest_accessible_palette(8, min_contrast=21.0)
        assert len(results) == 0


class TestSuggestReplacement:
    def test_passes_already_good(self):
        # Black on white is already accessible
        result = suggest_replacement((0, 0, 0), (255, 255, 255))
        assert result == (0, 0, 0)

    def test_fixes_low_contrast(self):
        # Light gray on white — should darken
        from altscribe.color.contrast import contrast_ratio

        result = suggest_replacement((200, 200, 200), (255, 255, 255))
        ratio = contrast_ratio(result, (255, 255, 255))
        assert ratio >= 4.5
        assert result != (200, 200, 200)
