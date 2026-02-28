"""Readability metrics analyzer — Flesch-Kincaid, Gunning Fog, etc."""

from __future__ import annotations

import panflute as pf

from altscribe.analytics.base import (
    AnalyzerResult,
    BaseAnalyzer,
    Metric,
    MetricCategory,
)


class ReadabilityAnalyzer(BaseAnalyzer):
    analyzer_id = "readability"
    analyzer_name = "Readability Metrics"
    category = MetricCategory.READABILITY
    element_types = (pf.Para, pf.Plain, pf.Header)

    def __init__(self) -> None:
        self._text_parts: list[str] = []

    def analyze(self, elem: pf.Element, doc: pf.Doc) -> None:
        text = pf.stringify(elem).strip()
        if text:
            self._text_parts.append(text)

    def finalize(self, doc: pf.Doc) -> AnalyzerResult:
        full_text = " ".join(self._text_parts)
        if len(full_text.split()) < 10:
            return self._make_result([])

        try:
            import textstat
        except ImportError:
            return self._make_result(
                [
                    Metric(
                        name="readability_error",
                        display_name="Readability Unavailable",
                        value="Install textstat: pip install altscribe[analytics]",
                        category=MetricCategory.READABILITY,
                    ),
                ]
            )

        metrics = [
            Metric(
                name="flesch_kincaid_grade",
                display_name="Flesch-Kincaid Grade Level",
                value=round(textstat.flesch_kincaid_grade(full_text), 1),
                unit="grade level",
                category=MetricCategory.READABILITY,
                range_min=0,
                range_max=18,
                interpretation="US school grade level needed to understand the text",
            ),
            Metric(
                name="flesch_reading_ease",
                display_name="Flesch Reading Ease",
                value=round(textstat.flesch_reading_ease(full_text), 1),
                unit="score",
                category=MetricCategory.READABILITY,
                range_min=0,
                range_max=100,
                interpretation=("Higher = easier. 60-70 = standard, 30-50 = college"),
            ),
            Metric(
                name="gunning_fog",
                display_name="Gunning Fog Index",
                value=round(textstat.gunning_fog(full_text), 1),
                unit="grade level",
                category=MetricCategory.READABILITY,
                range_min=0,
                range_max=20,
                interpretation="Years of education needed. 12+ = hard to read",
            ),
            Metric(
                name="smog_index",
                display_name="SMOG Index",
                value=round(textstat.smog_index(full_text), 1),
                unit="grade level",
                category=MetricCategory.READABILITY,
                range_min=0,
                range_max=20,
                interpretation="Years of education needed to understand",
            ),
            Metric(
                name="coleman_liau_index",
                display_name="Coleman-Liau Index",
                value=round(textstat.coleman_liau_index(full_text), 1),
                unit="grade level",
                category=MetricCategory.READABILITY,
                range_min=0,
                range_max=18,
            ),
            Metric(
                name="ari",
                display_name="Automated Readability Index",
                value=round(textstat.automated_readability_index(full_text), 1),
                unit="grade level",
                category=MetricCategory.READABILITY,
                range_min=0,
                range_max=18,
            ),
            Metric(
                name="dale_chall",
                display_name="Dale-Chall Readability Score",
                value=round(textstat.dale_chall_readability_score(full_text), 1),
                unit="score",
                category=MetricCategory.READABILITY,
                range_min=0,
                range_max=10,
                interpretation="4.9 or below = 4th grader. 9+ = college graduate",
            ),
        ]
        return self._make_result(metrics)
