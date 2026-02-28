"""Tests for color vision deficiency simulation."""

from altscribe.color.colorblind import CVDType, colors_distinguishable, simulate_cvd


class TestSimulateCVD:
    def test_black_unchanged(self):
        for cvd in CVDType:
            assert simulate_cvd((0, 0, 0), cvd) == (0, 0, 0)

    def test_white_unchanged(self):
        for cvd in CVDType:
            result = simulate_cvd((255, 255, 255), cvd)
            # Should be close to white (within rounding)
            assert all(c >= 250 for c in result)

    def test_protanopia_red_shift(self):
        # Red should lose its redness under protanopia
        sim = simulate_cvd((255, 0, 0), CVDType.PROTANOPIA)
        # R channel should decrease significantly, G should increase
        assert sim[0] < 255
        assert sim != (255, 0, 0)

    def test_output_in_range(self):
        for cvd in CVDType:
            result = simulate_cvd((128, 64, 192), cvd)
            assert all(0 <= c <= 255 for c in result)


class TestColorsDistinguishable:
    def test_black_white_always_distinguishable(self):
        for cvd in CVDType:
            assert colors_distinguishable((0, 0, 0), (255, 255, 255), cvd)

    def test_identical_colors_not_distinguishable(self):
        for cvd in CVDType:
            assert not colors_distinguishable((128, 128, 128), (128, 128, 128), cvd)
