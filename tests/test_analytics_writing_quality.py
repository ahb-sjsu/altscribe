"""Tests for writing quality analyzer."""

from pathlib import Path

from altscribe.processor import process_document


def _analyze(md: str, tmp_path: Path):
    """Run only the writing-quality analyzer."""
    _, _, analyzer_results = process_document(
        md,
        input_format="markdown",
        output_format="markdown",
        api_key="",
        base_dir=tmp_path,
        fix=False,
        enabled_checks=[],
        run_analytics=True,
        enabled_analyzers=["writing-quality"],
    )
    return analyzer_results[0]


class TestWritingQuality:
    def test_detects_passive_voice(self, tmp_path: Path):
        md = (
            "The report was written by the team. "
            "The data was collected last month. "
            "Active sentence here.\n"
        )
        result = _analyze(md, tmp_path)
        pv = result.get_metric("passive_voice_pct")
        assert pv is not None
        assert pv.value > 0

    def test_active_voice_low_passive(self, tmp_path: Path):
        md = (
            "The team wrote the report. "
            "We collected the data last month. "
            "The manager reviewed the results.\n"
        )
        result = _analyze(md, tmp_path)
        pv = result.get_metric("passive_voice_pct")
        assert pv is not None
        assert pv.value == 0

    def test_complex_sentence_detection(self, tmp_path: Path):
        md = (
            "Although the project was delayed because the funding was cut "
            "while the team was restructuring which caused additional problems "
            "that nobody had anticipated when the original plan was drafted "
            "by the committee.\n"
        )
        result = _analyze(md, tmp_path)
        cs = result.get_metric("complex_sentence_pct")
        assert cs is not None
        assert cs.value > 0

    def test_empty_document(self, tmp_path: Path):
        md = ""
        result = _analyze(md, tmp_path)
        assert len(result.metrics) == 0
