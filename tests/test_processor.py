"""Basic tests for altscribe processor."""

from pathlib import Path
from unittest.mock import patch

from altscribe.processor import process_document

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


def test_calls_vision_for_missing_alt(tmp_path: Path):
    with patch("altscribe.processor.generate_alt_text", return_value="A chart showing quarterly revenue growth") as mock:
        result = process_document(
            SAMPLE_MD,
            input_format="markdown",
            output_format="markdown",
            api_key="test-key",
            base_dir=tmp_path,
        )
    mock.assert_called_once()
    assert "A chart showing quarterly revenue growth" in result


def test_skips_images_with_existing_alt(tmp_path: Path):
    with patch("altscribe.processor.generate_alt_text") as mock:
        process_document(
            SAMPLE_MD_WITH_ALT,
            input_format="markdown",
            output_format="markdown",
            api_key="test-key",
            base_dir=tmp_path,
        )
    mock.assert_not_called()


def test_overwrite_forces_regeneration(tmp_path: Path):
    with patch("altscribe.processor.generate_alt_text", return_value="Updated description") as mock:
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
