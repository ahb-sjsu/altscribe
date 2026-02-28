"""Tests for list structure checker."""

from pathlib import Path

from altscribe.processor import process_document


def _check(md: str, tmp_path: Path, fix: bool = False, fmt: str = "markdown"):
    """Run only the list-structure check."""
    result_text, results = process_document(
        md,
        input_format=fmt,
        output_format="markdown",
        api_key="",
        base_dir=tmp_path,
        fix=fix,
        enabled_checks=["list-structure"],
    )
    return result_text, results[0]


class TestListStructure:
    def test_detects_fake_bullet_list_html(self, tmp_path: Path):
        html = (
            "<p>\u2022 First item</p>\n"
            "<p>\u2022 Second item</p>\n"
            "<p>\u2022 Third item</p>\n"
        )
        _, result = _check(html, tmp_path, fmt="html")
        assert len(result.issues) >= 1
        assert any("bulleted" in i.message for i in result.issues)

    def test_detects_fake_ordered_list_html(self, tmp_path: Path):
        html = (
            "<p>1. First item</p>\n" "<p>2. Second item</p>\n" "<p>3. Third item</p>\n"
        )
        _, result = _check(html, tmp_path, fmt="html")
        assert len(result.issues) >= 1
        assert any("numbered" in i.message for i in result.issues)

    def test_ignores_single_item(self, tmp_path: Path):
        html = "<p>\u2022 Only one item</p>\n"
        _, result = _check(html, tmp_path, fmt="html")
        assert len(result.issues) == 0

    def test_fix_converts_to_list(self, tmp_path: Path):
        html = "<p>\u2022 First item</p>\n" "<p>\u2022 Second item</p>\n"
        _, result = _check(html, tmp_path, fix=True, fmt="html")
        fixed = [i for i in result.issues if i.fixed]
        assert len(fixed) >= 1

    def test_does_not_flag_real_lists(self, tmp_path: Path):
        md = "- Item one\n- Item two\n- Item three\n"
        _, result = _check(md, tmp_path)
        assert len(result.issues) == 0
