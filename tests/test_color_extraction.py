"""Tests for color extraction from HTML."""

from altscribe.color.extraction import extract_color_pairs, parse_color


class TestParseColor:
    def test_hex6(self):
        assert parse_color("#ff0000") == (255, 0, 0)

    def test_hex3(self):
        assert parse_color("#f00") == (255, 0, 0)

    def test_hex_case_insensitive(self):
        assert parse_color("#FF0000") == (255, 0, 0)

    def test_rgb(self):
        assert parse_color("rgb(255, 128, 0)") == (255, 128, 0)

    def test_rgba(self):
        assert parse_color("rgba(255, 128, 0, 0.5)") == (255, 128, 0)

    def test_named_color(self):
        assert parse_color("red") == (255, 0, 0)
        assert parse_color("navy") == (0, 0, 128)

    def test_named_case_insensitive(self):
        assert parse_color("Red") == (255, 0, 0)

    def test_unknown_returns_none(self):
        assert parse_color("not-a-color") is None

    def test_whitespace_stripped(self):
        assert parse_color("  #ff0000  ") == (255, 0, 0)


class TestExtractColorPairs:
    def test_inline_style_fg_only(self):
        html = '<p style="color: #ff0000">Red text</p>'
        pairs = extract_color_pairs(html)
        assert len(pairs) == 1
        assert pairs[0].foreground == (255, 0, 0)
        assert pairs[0].background == (255, 255, 255)  # default

    def test_inline_style_fg_and_bg(self):
        html = '<p style="color: white; background-color: #333">Text</p>'
        pairs = extract_color_pairs(html)
        assert len(pairs) == 1
        assert pairs[0].foreground == (255, 255, 255)
        assert pairs[0].background == (51, 51, 51)

    def test_bgcolor_attribute(self):
        html = '<table bgcolor="#ffcc00"><tr><td>Cell</td></tr></table>'
        pairs = extract_color_pairs(html)
        assert len(pairs) >= 1
        bg_pair = [p for p in pairs if p.background == (255, 204, 0)]
        assert len(bg_pair) == 1

    def test_font_color(self):
        html = '<font color="blue">Old school</font>'
        pairs = extract_color_pairs(html)
        assert len(pairs) == 1
        assert pairs[0].foreground == (0, 0, 255)

    def test_no_colors(self):
        html = "<p>Plain text with no colors</p>"
        pairs = extract_color_pairs(html)
        assert len(pairs) == 0

    def test_multiple_styles(self):
        html = '<p style="color: red">Red</p>' '<p style="color: blue">Blue</p>'
        pairs = extract_color_pairs(html)
        assert len(pairs) == 2
