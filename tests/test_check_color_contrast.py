"""Tests for the color contrast checker."""

from pathlib import Path

from altscribe.processor import process_document


def _check(html: str, tmp_path: Path, fix: bool = False):
    """Run only the color-contrast check on HTML input."""
    _, results, _ = process_document(
        html,
        input_format="html",
        output_format="html",
        api_key="",
        base_dir=tmp_path,
        fix=fix,
        enabled_checks=["color-contrast"],
    )
    return results[0]


class TestColorContrast:
    def test_detects_low_contrast(self, tmp_path: Path):
        html = '<p style="color: #cccccc; background-color: #ffffff">Light text</p>'
        result = _check(html, tmp_path)
        assert result.error_count >= 1
        assert any("Insufficient contrast" in i.message for i in result.issues)

    def test_passes_good_contrast(self, tmp_path: Path):
        html = '<p style="color: #000000; background-color: #ffffff">Black on white</p>'
        result = _check(html, tmp_path)
        contrast_errors = [
            i for i in result.issues if "Insufficient contrast" in i.message
        ]
        assert len(contrast_errors) == 0

    def test_no_issues_for_plain_html(self, tmp_path: Path):
        html = "<p>No inline styles here</p>"
        result = _check(html, tmp_path)
        assert len(result.issues) == 0

    def test_fix_suggests_replacement(self, tmp_path: Path):
        html = '<p style="color: #cccccc; background-color: #ffffff">Light text</p>'
        result = _check(html, tmp_path, fix=True)
        fixed = [i for i in result.issues if i.fixed]
        assert len(fixed) >= 1
        assert any("Suggested" in i.fix_description for i in fixed)

    def test_no_issues_for_markdown(self, tmp_path: Path):
        """Markdown has no colors, so no issues should be reported."""
        _, results, _ = process_document(
            "# Hello\n\nPlain markdown.\n",
            input_format="markdown",
            output_format="markdown",
            api_key="",
            base_dir=tmp_path,
            fix=False,
            enabled_checks=["color-contrast"],
        )
        result = results[0]
        assert len(result.issues) == 0
