"""Tests for altscribe processor — covers all W3C WAI image categories."""

from pathlib import Path
from unittest.mock import patch

from altscribe.processor import process_document
from altscribe.vision import AltTextResult, ImageType

SAMPLE_MD = """\
# Hello

Here is a paragraph.

![](test.png)

More text after the image.
"""

SAMPLE_MD_WITH_ALT = """\
# Hello

![A cute cat sitting on a windowsill](cat.png)
"""

SAMPLE_MD_LINKED_IMAGE = """\
# Navigation

[![](logo.png)](https://example.com)
"""

SAMPLE_MD_MULTIPLE = """\
# Report

![](chart.png)

Some analysis text.

![](photo.png)
"""


def _informative(alt: str) -> AltTextResult:
    return AltTextResult(image_type=ImageType.INFORMATIVE, alt_text=alt)


def _decorative() -> AltTextResult:
    return AltTextResult(image_type=ImageType.DECORATIVE, alt_text="")


def _functional(alt: str) -> AltTextResult:
    return AltTextResult(image_type=ImageType.FUNCTIONAL, alt_text=alt)


def _complex(alt: str, long_desc: str) -> AltTextResult:
    return AltTextResult(
        image_type=ImageType.COMPLEX,
        alt_text=alt,
        long_description=long_desc,
    )


def _text(alt: str) -> AltTextResult:
    return AltTextResult(image_type=ImageType.TEXT, alt_text=alt)


class TestInformativeImages:
    def test_generates_alt_for_missing(self, tmp_path: Path):
        result_obj = _informative("A chart showing quarterly revenue growth")
        with patch(
            "altscribe.processor.generate_alt_text",
            return_value=result_obj,
        ) as mock:
            result = process_document(
                SAMPLE_MD,
                input_format="markdown",
                output_format="markdown",
                api_key="test-key",
                base_dir=tmp_path,
            )
        mock.assert_called_once()
        assert "A chart showing quarterly revenue growth" in result

    def test_skips_images_with_existing_alt(self, tmp_path: Path):
        with patch("altscribe.processor.generate_alt_text") as mock:
            process_document(
                SAMPLE_MD_WITH_ALT,
                input_format="markdown",
                output_format="markdown",
                api_key="test-key",
                base_dir=tmp_path,
            )
        mock.assert_not_called()

    def test_overwrite_forces_regeneration(self, tmp_path: Path):
        result_obj = _informative("Updated description")
        with patch(
            "altscribe.processor.generate_alt_text",
            return_value=result_obj,
        ) as mock:
            result = process_document(
                SAMPLE_MD_WITH_ALT,
                input_format="markdown",
                output_format="markdown",
                api_key="test-key",
                base_dir=tmp_path,
                overwrite=True,
            )
        mock.assert_called_once()
        assert "Updated description" in result


class TestDecorativeImages:
    def test_decorative_produces_empty_alt(self, tmp_path: Path):
        with patch(
            "altscribe.processor.generate_alt_text",
            return_value=_decorative(),
        ) as mock:
            result = process_document(
                SAMPLE_MD,
                input_format="markdown",
                output_format="html",
                api_key="test-key",
                base_dir=tmp_path,
            )
        mock.assert_called_once()
        assert 'alt=""' in result
        assert 'role="presentation"' in result


class TestFunctionalImages:
    def test_functional_passes_link_context(self, tmp_path: Path):
        result_obj = _functional("Navigate to example.com homepage")
        with patch(
            "altscribe.processor.generate_alt_text",
            return_value=result_obj,
        ) as mock:
            result = process_document(
                SAMPLE_MD_LINKED_IMAGE,
                input_format="markdown",
                output_format="markdown",
                api_key="test-key",
                base_dir=tmp_path,
            )
        mock.assert_called_once()
        call_kwargs = mock.call_args
        assert call_kwargs.kwargs.get("is_functional") or (
            len(call_kwargs.args) > 4 and call_kwargs.args[4]
        )
        assert "Navigate to example.com homepage" in result


class TestComplexImages:
    def test_complex_adds_long_description(self, tmp_path: Path):
        result_obj = _complex(
            "Bar chart of Q1-Q4 revenue",
            "The bar chart shows revenue increasing from $1M in Q1 to $4M in Q4.",
        )
        with patch(
            "altscribe.processor.generate_alt_text",
            return_value=result_obj,
        ) as mock:
            result = process_document(
                SAMPLE_MD,
                input_format="markdown",
                output_format="markdown",
                api_key="test-key",
                base_dir=tmp_path,
            )
        mock.assert_called_once()
        assert "Bar chart of Q1-Q4 revenue" in result
        assert "revenue increasing from" in result


class TestTextImages:
    def test_text_image_transcribes(self, tmp_path: Path):
        result_obj = _text("Welcome to California State University")
        with patch(
            "altscribe.processor.generate_alt_text",
            return_value=result_obj,
        ) as mock:
            result = process_document(
                SAMPLE_MD,
                input_format="markdown",
                output_format="markdown",
                api_key="test-key",
                base_dir=tmp_path,
            )
        mock.assert_called_once()
        assert "Welcome to California State University" in result


class TestMultipleImages:
    def test_processes_all_images(self, tmp_path: Path):
        results = [
            _complex(
                "Revenue chart",
                "Chart shows steady growth across all quarters.",
            ),
            _informative("Team photo at annual retreat"),
        ]
        with patch(
            "altscribe.processor.generate_alt_text",
            side_effect=results,
        ) as mock:
            result = process_document(
                SAMPLE_MD_MULTIPLE,
                input_format="markdown",
                output_format="markdown",
                api_key="test-key",
                base_dir=tmp_path,
            )
        assert mock.call_count == 2
        assert "Revenue chart" in result
        assert "Team photo at annual retreat" in result


class TestErrorHandling:
    def test_continues_on_failure(self, tmp_path: Path):
        with patch(
            "altscribe.processor.generate_alt_text",
            side_effect=Exception("API error"),
        ):
            result = process_document(
                SAMPLE_MD,
                input_format="markdown",
                output_format="markdown",
                api_key="test-key",
                base_dir=tmp_path,
            )
        # Should still produce output, just without alt text
        assert "test.png" in result
