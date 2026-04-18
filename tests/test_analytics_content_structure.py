"""Tests for content structure analyzer."""

from pathlib import Path

from altscribe.processor import process_document


def _analyze(md: str, tmp_path: Path):
    """Run only the content-structure analyzer."""
    _, _, analyzer_results = process_document(
        md,
        input_format="markdown",
        output_format="markdown",
        api_key="",
        base_dir=tmp_path,
        fix=False,
        enabled_checks=[],
        run_analytics=True,
        enabled_analyzers=["content-structure"],
    )
    return analyzer_results[0]


class TestContentStructure:
    def test_counts_images(self, tmp_path: Path):
        md = "![alt1](a.png)\n\n![alt2](b.png)\n\nSome text.\n"
        result = _analyze(md, tmp_path)
        ic = result.get_metric("image_count")
        assert ic is not None
        assert ic.value == 2

    def test_counts_headings(self, tmp_path: Path):
        md = "# H1\n\n## H2\n\n### H3\n\nParagraph text here.\n"
        result = _analyze(md, tmp_path)
        hc = result.get_metric("heading_count")
        assert hc is not None
        assert hc.value == 3

    def test_counts_links(self, tmp_path: Path):
        md = "[Link 1](http://a.com) and [Link 2](http://b.com).\n"
        result = _analyze(md, tmp_path)
        lc = result.get_metric("link_count")
        assert lc is not None
        assert lc.value == 2

    def test_image_to_text_ratio(self, tmp_path: Path):
        md = "![img](a.png)\n\n" + ("word " * 100) + "\n"
        result = _analyze(md, tmp_path)
        ratio = result.get_metric("image_to_text_ratio")
        assert ratio is not None
        assert 5 < ratio.value < 15  # ~10 images per 1000 words

    def test_empty_document(self, tmp_path: Path):
        md = ""
        result = _analyze(md, tmp_path)
        ic = result.get_metric("image_count")
        assert ic is not None
        assert ic.value == 0
