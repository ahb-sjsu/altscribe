"""Tests for altscribe processor — covers the dispatch + image alt-text path."""

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


def _process(md, tmp_path, mock_return=None, **kwargs):
    """Helper to run process_document with only image-alt-text enabled."""
    defaults = {
        "input_format": "markdown",
        "output_format": "markdown",
        "api_key": "test-key",
        "base_dir": tmp_path,
        "enabled_checks": ["image-alt-text"],
    }
    defaults.update(kwargs)
    if mock_return is not None:
        with patch(
            "altscribe.checks.image_alt_text.generate_alt_text",
            return_value=mock_return,
        ) as mock:
            result, checks = process_document(md, **defaults)
            return result, checks, mock
    result, checks = process_document(md, **defaults)
    return result, checks, None


class TestInformativeImages:
    def test_generates_alt_for_missing(self, tmp_path: Path):
        result, _, mock = _process(
            SAMPLE_MD,
            tmp_path,
            mock_return=_informative("A chart showing quarterly revenue growth"),
        )
        mock.assert_called_once()
        assert "A chart showing quarterly revenue growth" in result

    def test_skips_images_with_existing_alt(self, tmp_path: Path):
        with patch("altscribe.checks.image_alt_text.generate_alt_text") as mock:
            process_document(
                SAMPLE_MD_WITH_ALT,
                input_format="markdown",
                output_format="markdown",
                api_key="test-key",
                base_dir=tmp_path,
                enabled_checks=["image-alt-text"],
            )
        mock.assert_not_called()

    def test_overwrite_forces_regeneration(self, tmp_path: Path):
        result, _, mock = _process(
            SAMPLE_MD_WITH_ALT,
            tmp_path,
            mock_return=_informative("Updated description"),
            overwrite=True,
        )
        mock.assert_called_once()
        assert "Updated description" in result


class TestDecorativeImages:
    def test_decorative_produces_empty_alt(self, tmp_path: Path):
        result, _, mock = _process(
            SAMPLE_MD,
            tmp_path,
            mock_return=_decorative(),
            output_format="html",
        )
        mock.assert_called_once()
        assert 'alt=""' in result
        assert 'role="presentation"' in result


class TestFunctionalImages:
    def test_functional_passes_link_context(self, tmp_path: Path):
        result, _, mock = _process(
            SAMPLE_MD_LINKED_IMAGE,
            tmp_path,
            mock_return=_functional("Navigate to example.com homepage"),
        )
        mock.assert_called_once()
        assert "Navigate to example.com homepage" in result


class TestComplexImages:
    def test_complex_adds_long_description(self, tmp_path: Path):
        result, _, mock = _process(
            SAMPLE_MD,
            tmp_path,
            mock_return=_complex(
                "Bar chart of Q1-Q4 revenue",
                "The bar chart shows revenue increasing from $1M in Q1 to $4M in Q4.",
            ),
        )
        mock.assert_called_once()
        assert "Bar chart of Q1-Q4 revenue" in result
        assert "revenue increasing from" in result


class TestTextImages:
    def test_text_image_transcribes(self, tmp_path: Path):
        result, _, mock = _process(
            SAMPLE_MD,
            tmp_path,
            mock_return=_text("Welcome to California State University"),
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
            "altscribe.checks.image_alt_text.generate_alt_text",
            side_effect=results,
        ) as mock:
            result, _ = process_document(
                SAMPLE_MD_MULTIPLE,
                input_format="markdown",
                output_format="markdown",
                api_key="test-key",
                base_dir=tmp_path,
                enabled_checks=["image-alt-text"],
            )
        assert mock.call_count == 2
        assert "Revenue chart" in result
        assert "Team photo at annual retreat" in result


class TestErrorHandling:
    def test_continues_on_failure(self, tmp_path: Path):
        with patch(
            "altscribe.checks.image_alt_text.generate_alt_text",
            side_effect=Exception("API error"),
        ):
            result, _ = process_document(
                SAMPLE_MD,
                input_format="markdown",
                output_format="markdown",
                api_key="test-key",
                base_dir=tmp_path,
                enabled_checks=["image-alt-text"],
            )
        assert "test.png" in result
