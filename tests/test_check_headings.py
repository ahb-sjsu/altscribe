"""Tests for heading hierarchy checker."""

from pathlib import Path

from altscribe.checks.base import Severity
from altscribe.processor import process_document


def _check(md: str, tmp_path: Path, fix: bool = False):
    """Run only the heading-hierarchy check."""
    _, results, _ = process_document(
        md,
        input_format="markdown",
        output_format="markdown",
        api_key="",
        base_dir=tmp_path,
        fix=fix,
        enabled_checks=["heading-hierarchy"],
    )
    return results[0]


class TestHeadingHierarchy:
    def test_detects_missing_h1(self, tmp_path: Path):
        md = "## Section\n\n### Subsection\n"
        result = _check(md, tmp_path)
        messages = [i.message for i in result.issues]
        assert any("no H1" in m for m in messages)

    def test_detects_skipped_levels(self, tmp_path: Path):
        md = "# Title\n\n### Skipped\n"
        result = _check(md, tmp_path)
        messages = [i.message for i in result.issues]
        assert any("Skipped" in m for m in messages)

    def test_fixes_skipped_levels(self, tmp_path: Path):
        md = "# Title\n\n### Skipped\n"
        result = _check(md, tmp_path, fix=True)
        fixed = [i for i in result.issues if i.fixed]
        assert len(fixed) >= 1
        assert any("Re-leveled" in i.fix_description for i in fixed)

    def test_detects_empty_heading(self, tmp_path: Path):
        md = "# \n\nSome text\n"
        result = _check(md, tmp_path)
        messages = [i.message for i in result.issues]
        assert any("Empty heading" in m for m in messages)

    def test_detects_fake_heading(self, tmp_path: Path):
        md = "# Real Heading\n\n**This looks like a heading**\n\nParagraph.\n"
        result = _check(md, tmp_path)
        warnings = [i for i in result.issues if i.severity == Severity.WARNING]
        assert any("Fake heading" in w.message for w in warnings)

    def test_promotes_fake_heading(self, tmp_path: Path):
        md = "# Real Heading\n\n**This looks like a heading**\n\nParagraph.\n"
        result = _check(md, tmp_path, fix=True)
        fixed = [i for i in result.issues if i.fixed]
        assert any("Promoted" in i.fix_description for i in fixed)

    def test_no_false_positive_on_mixed_para(self, tmp_path: Path):
        md = "# Title\n\n**Bold** and regular text.\n"
        result = _check(md, tmp_path)
        warnings = [i for i in result.issues if "Fake heading" in i.message]
        assert len(warnings) == 0

    def test_clean_document(self, tmp_path: Path):
        md = "# Title\n\n## Section\n\n### Subsection\n"
        result = _check(md, tmp_path)
        assert result.error_count == 0
