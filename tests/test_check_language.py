"""Tests for document language checker."""

from pathlib import Path

from altscribe.processor import process_document


def _check(md: str, tmp_path: Path, fix: bool = False):
    """Run only the document-language check."""
    _, results = process_document(
        md,
        input_format="markdown",
        output_format="markdown",
        api_key="",
        base_dir=tmp_path,
        fix=fix,
        enabled_checks=["document-language"],
    )
    return results[0]


class TestDocumentLanguage:
    def test_detects_missing_lang(self, tmp_path: Path):
        md = "# Hello\n\nSome text.\n"
        result = _check(md, tmp_path)
        assert result.error_count >= 1
        assert any("lang" in i.message for i in result.issues)

    def test_passes_with_lang(self, tmp_path: Path):
        md = "---\nlang: en\n---\n\n# Hello\n"
        result = _check(md, tmp_path)
        assert result.error_count == 0

    def test_fix_sets_lang(self, tmp_path: Path):
        md = "# Hello\n\nSome English text here.\n"
        result = _check(md, tmp_path, fix=True)
        fixed = [i for i in result.issues if i.fixed]
        assert len(fixed) >= 1
        assert any("lang=" in i.fix_description for i in fixed)
