"""Tests for altscribe vision module."""

from altscribe.vision import AltTextResult, ImageType, _parse_response


class TestParseResponse:
    def test_plain_json(self):
        raw = (
            '{"image_type": "informative",'
            ' "alt_text": "A dog",'
            ' "long_description": null}'
        )
        data = _parse_response(raw)
        assert data["image_type"] == "informative"
        assert data["alt_text"] == "A dog"

    def test_json_with_markdown_fences(self):
        raw = (
            "```json\n"
            '{"image_type": "decorative",'
            ' "alt_text": "",'
            ' "long_description": null}\n'
            "```"
        )
        data = _parse_response(raw)
        assert data["image_type"] == "decorative"
        assert data["alt_text"] == ""

    def test_json_with_bare_fences(self):
        raw = (
            "```\n"
            '{"image_type": "text",'
            ' "alt_text": "Hello World",'
            ' "long_description": null}\n'
            "```"
        )
        data = _parse_response(raw)
        assert data["image_type"] == "text"
        assert data["alt_text"] == "Hello World"


class TestAltTextResult:
    def test_informative_result(self):
        result = AltTextResult(
            image_type=ImageType.INFORMATIVE,
            alt_text="Students in a lecture hall",
        )
        assert result.image_type == ImageType.INFORMATIVE
        assert result.long_description is None

    def test_complex_result(self):
        result = AltTextResult(
            image_type=ImageType.COMPLEX,
            alt_text="Enrollment trends 2020-2025",
            long_description="Line chart showing enrollment rising from 40k to 55k.",
        )
        assert result.long_description is not None

    def test_decorative_result(self):
        result = AltTextResult(
            image_type=ImageType.DECORATIVE,
            alt_text="",
        )
        assert result.alt_text == ""
