"""Tests for table accessibility checker."""

from pathlib import Path

from altscribe.processor import process_document

TABLE_MD = """\
| Col A | Col B |
|-------|-------|
| 1     | 2     |
| 3     | 4     |
"""

TABLE_HTML_NO_HEADER = """\
<table>
<tr><td>A</td><td>B</td></tr>
<tr><td>1</td><td>2</td></tr>
</table>
"""


def _check(md: str, tmp_path: Path, fix: bool = False, fmt: str = "markdown"):
    """Run only the table-accessibility check."""
    _, results, _ = process_document(
        md,
        input_format=fmt,
        output_format="markdown",
        api_key="",
        base_dir=tmp_path,
        fix=fix,
        enabled_checks=["table-accessibility"],
    )
    return results[0]


class TestTableAccessibility:
    def test_detects_missing_caption(self, tmp_path: Path):
        result = _check(TABLE_MD, tmp_path)
        assert any("missing caption" in i.message for i in result.issues)

    def test_no_issues_for_doc_without_tables(self, tmp_path: Path):
        md = "# Hello\n\nJust text.\n"
        result = _check(md, tmp_path)
        assert len(result.issues) == 0
