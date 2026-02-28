"""Tests for readability metrics analyzer."""

from pathlib import Path

import pytest

from altscribe.processor import process_document

try:
    import textstat  # noqa: F401

    HAS_TEXTSTAT = True
except ImportError:
    HAS_TEXTSTAT = False


def _analyze(md: str, tmp_path: Path):
    """Run only the readability analyzer."""
    _, _, analyzer_results = process_document(
        md,
        input_format="markdown",
        output_format="markdown",
        api_key="",
        base_dir=tmp_path,
        fix=False,
        enabled_checks=[],
        run_analytics=True,
        enabled_analyzers=["readability"],
    )
    return analyzer_results[0]


@pytest.mark.skipif(not HAS_TEXTSTAT, reason="textstat not installed")
class TestReadability:
    def test_simple_text_low_grade(self, tmp_path: Path):
        md = "The cat sat on the mat. The dog ran fast. It was a sunny day.\n"
        result = _analyze(md, tmp_path)
        fk = result.get_metric("flesch_kincaid_grade")
        assert fk is not None
        assert fk.value < 6

    def test_all_seven_metrics_present(self, tmp_path: Path):
        md = (
            "# Report\n\n"
            + ("This is a moderately complex sentence with several words. " * 20)
            + "\n"
        )
        result = _analyze(md, tmp_path)
        expected = {
            "flesch_kincaid_grade",
            "flesch_reading_ease",
            "gunning_fog",
            "smog_index",
            "coleman_liau_index",
            "ari",
            "dale_chall",
        }
        actual = {m.name for m in result.metrics}
        assert expected == actual

    def test_short_text_returns_no_metrics(self, tmp_path: Path):
        md = "Hello world.\n"
        result = _analyze(md, tmp_path)
        assert len(result.metrics) == 0

    def test_flesch_reading_ease_range(self, tmp_path: Path):
        md = (
            "The cat sat on the mat. "
            "The dog ran in the yard. "
            "Birds sang in the trees. "
            "Fish swam in the pond. "
            "The sun was bright today.\n"
        )
        result = _analyze(md, tmp_path)
        fre = result.get_metric("flesch_reading_ease")
        assert fre is not None
        assert 0 <= fre.value <= 120
