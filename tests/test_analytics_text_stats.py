"""Tests for text statistics analyzer."""

from pathlib import Path

from altscribe.processor import process_document


def _analyze(md: str, tmp_path: Path):
    """Run only the text-statistics analyzer."""
    _, _, analyzer_results = process_document(
        md,
        input_format="markdown",
        output_format="markdown",
        api_key="",
        base_dir=tmp_path,
        fix=False,
        enabled_checks=[],
        run_analytics=True,
        enabled_analyzers=["text-statistics"],
    )
    return analyzer_results[0]


class TestTextStatistics:
    def test_word_count(self, tmp_path: Path):
        md = "The cat sat on the mat.\n"
        result = _analyze(md, tmp_path)
        wc = result.get_metric("word_count")
        assert wc is not None
        assert wc.value == 6

    def test_paragraph_count(self, tmp_path: Path):
        md = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph.\n"
        result = _analyze(md, tmp_path)
        pc = result.get_metric("paragraph_count")
        assert pc is not None
        assert pc.value == 3

    def test_vocabulary_diversity(self, tmp_path: Path):
        md = "The cat sat. The cat slept. The cat ran.\n"
        result = _analyze(md, tmp_path)
        ttr = result.get_metric("vocabulary_diversity")
        assert ttr is not None
        assert 0 < ttr.value < 1

    def test_avg_sentence_length(self, tmp_path: Path):
        md = "One two three. Four five six.\n"
        result = _analyze(md, tmp_path)
        asl = result.get_metric("avg_sentence_length")
        assert asl is not None
        assert asl.value == 3.0

    def test_empty_document(self, tmp_path: Path):
        md = ""
        _, _, analyzer_results = process_document(
            md,
            input_format="markdown",
            output_format="markdown",
            api_key="",
            base_dir=tmp_path,
            fix=False,
            enabled_checks=[],
            run_analytics=True,
            enabled_analyzers=["text-statistics"],
        )
        result = analyzer_results[0]
        wc = result.get_metric("word_count")
        assert wc is not None
        assert wc.value == 0
