"""Content structure analyzer — images, tables, headings, ratios."""

from __future__ import annotations

import panflute as pf

from altscribe.analytics.base import (
    AnalyzerResult,
    BaseAnalyzer,
    Metric,
    MetricCategory,
)


class ContentStructureAnalyzer(BaseAnalyzer):
    analyzer_id = "content-structure"
    analyzer_name = "Content Structure"
    category = MetricCategory.CONTENT_STRUCTURE
    element_types = (pf.Image, pf.Table, pf.Header, pf.Para, pf.Plain, pf.Link)

    def __init__(self) -> None:
        self._image_count = 0
        self._table_count = 0
        self._heading_count = 0
        self._link_count = 0
        self._word_count = 0
        self._para_count = 0

    def analyze(self, elem: pf.Element, doc: pf.Doc) -> None:
        if isinstance(elem, pf.Image):
            self._image_count += 1
        elif isinstance(elem, pf.Table):
            self._table_count += 1
        elif isinstance(elem, pf.Header):
            self._heading_count += 1
        elif isinstance(elem, pf.Link):
            self._link_count += 1
        elif isinstance(elem, (pf.Para, pf.Plain)):
            self._para_count += 1
            text = pf.stringify(elem)
            self._word_count += len(text.split())

    def finalize(self, doc: pf.Doc) -> AnalyzerResult:
        img_to_text = round(self._image_count / max(self._word_count, 1) * 1000, 2)
        heading_density = round(self._heading_count / max(self._para_count, 1) * 100, 1)

        metrics = [
            Metric(
                name="image_count",
                display_name="Images",
                value=self._image_count,
                category=MetricCategory.CONTENT_STRUCTURE,
            ),
            Metric(
                name="table_count",
                display_name="Tables",
                value=self._table_count,
                category=MetricCategory.CONTENT_STRUCTURE,
            ),
            Metric(
                name="heading_count",
                display_name="Headings",
                value=self._heading_count,
                category=MetricCategory.CONTENT_STRUCTURE,
            ),
            Metric(
                name="link_count",
                display_name="Links",
                value=self._link_count,
                category=MetricCategory.CONTENT_STRUCTURE,
            ),
            Metric(
                name="image_to_text_ratio",
                display_name="Image-to-Text Ratio",
                value=img_to_text,
                unit="images per 1000 words",
                category=MetricCategory.CONTENT_STRUCTURE,
                interpretation="Higher values indicate more visual content",
            ),
            Metric(
                name="heading_density",
                display_name="Heading Density",
                value=heading_density,
                unit="%",
                category=MetricCategory.CONTENT_STRUCTURE,
                interpretation="Headings-to-paragraphs. Higher = organized",
            ),
        ]
        return self._make_result(metrics)
