"""Tests for WCAG contrast ratio computation."""

from altscribe.color.contrast import (
    check_contrast,
    contrast_ratio,
    relative_luminance,
)


class TestRelativeLuminance:
    def test_black(self):
        assert relative_luminance((0, 0, 0)) == 0.0

    def test_white(self):
        assert abs(relative_luminance((255, 255, 255)) - 1.0) < 0.01

    def test_mid_gray(self):
        lum = relative_luminance((128, 128, 128))
        assert 0.2 < lum < 0.3


class TestContrastRatio:
    def test_black_on_white(self):
        ratio = contrast_ratio((0, 0, 0), (255, 255, 255))
        assert abs(ratio - 21.0) < 0.1

    def test_white_on_white(self):
        ratio = contrast_ratio((255, 255, 255), (255, 255, 255))
        assert abs(ratio - 1.0) < 0.01

    def test_symmetric(self):
        r1 = contrast_ratio((255, 0, 0), (0, 0, 255))
        r2 = contrast_ratio((0, 0, 255), (255, 0, 0))
        assert abs(r1 - r2) < 0.01


class TestCheckContrast:
    def test_aa_normal_pass(self):
        result = check_contrast((0, 0, 0), (255, 255, 255))
        assert result.aa_normal is True
        assert result.aaa_normal is True

    def test_aa_normal_fail(self):
        # Light gray on white — low contrast
        result = check_contrast((200, 200, 200), (255, 255, 255))
        assert result.aa_normal is False
        assert result.ratio < 4.5

    def test_aa_large_pass(self):
        # Medium gray on white may pass large text (3:1) but fail normal (4.5:1)
        result = check_contrast((119, 119, 119), (255, 255, 255))
        assert result.aa_large is True
