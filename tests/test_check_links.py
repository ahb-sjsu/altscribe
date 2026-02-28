"""Tests for link text quality checker."""

from pathlib import Path

from altscribe.checks.base import Severity
from altscribe.processor import process_document


def _check(md: str, tmp_path: Path, fix: bool = False):
    """Run only the link-text check."""
    _, results, _ = process_document(
        md,
        input_format="markdown",
        output_format="markdown",
        api_key="",
        base_dir=tmp_path,
        fix=fix,
        enabled_checks=["link-text"],
    )
    return results[0]


class TestLinkText:
    def test_detects_click_here(self, tmp_path: Path):
        md = "[click here](https://example.com)\n"
        result = _check(md, tmp_path)
        assert result.error_count >= 1
        assert any("Generic link text" in i.message for i in result.issues)

    def test_detects_here(self, tmp_path: Path):
        md = "[here](https://example.com)\n"
        result = _check(md, tmp_path)
        assert result.error_count >= 1

    def test_detects_empty_link(self, tmp_path: Path):
        md = "[](https://example.com)\n"
        result = _check(md, tmp_path)
        assert any("no text" in i.message for i in result.issues)

    def test_detects_bare_url(self, tmp_path: Path):
        md = "[https://example.com](https://example.com)\n"
        result = _check(md, tmp_path)
        assert any("Bare URL" in i.message for i in result.issues)

    def test_detects_short_text(self, tmp_path: Path):
        md = "[X](https://example.com)\n"
        result = _check(md, tmp_path)
        warnings = [i for i in result.issues if i.severity == Severity.WARNING]
        assert any("too short" in w.message for w in warnings)

    def test_detects_duplicate_different_urls(self, tmp_path: Path):
        md = (
            "[Download](https://example.com/a.pdf)\n\n"
            "[Download](https://example.com/b.pdf)\n"
        )
        result = _check(md, tmp_path)
        warnings = [i for i in result.issues if i.severity == Severity.WARNING]
        assert any("Duplicate link text" in w.message for w in warnings)

    def test_passes_good_link_text(self, tmp_path: Path):
        md = "[Download the 2025 annual report](https://example.com/report.pdf)\n"
        result = _check(md, tmp_path)
        assert len(result.issues) == 0

    def test_passes_learn_more_variants(self, tmp_path: Path):
        md = "[learn more](https://example.com)\n"
        result = _check(md, tmp_path)
        assert result.error_count >= 1
