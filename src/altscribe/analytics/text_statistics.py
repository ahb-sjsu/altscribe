"""Text statistics analyzer — word count, sentence count, vocabulary diversity."""

from __future__ import annotations

import re

import panflute as pf

from altscribe.analytics.base import (
    AnalyzerResult,
    BaseAnalyzer,
    Metric,
    MetricCategory,
)


class TextStatisticsAnalyzer(BaseAnalyzer):
    analyzer_id = "text-statistics"
    analyzer_name = "Text Statistics"
    category = MetricCategory.TEXT_STATISTICS
    element_types = (pf.Para, pf.Plain, pf.Header)

    def __init__(self) -> None:
        self._paragraphs: list[str] = []
        self._all_words: list[str] = []

    def analyze(self, elem: pf.Element, doc: pf.Doc) -> None:
        text = pf.stringify(elem).strip()
        if not text:
            return
        if isinstance(elem, (pf.Para, pf.Plain)):
            self._paragraphs.append(text)
        words = re.findall(r"\b\w+\b", text.lower())
        self._all_words.extend(words)

    def finalize(self, doc: pf.Doc) -> AnalyzerResult:
        word_count = len(self._all_words)
        unique_words = len(set(self._all_words))
        ttr = round(unique_words / word_count, 3) if word_count > 0 else 0

        # Simple sentence counting via punctuation boundaries
        full_text = " ".join(self._paragraphs)
        sentence_count = len(re.findall(r"[.!?]+", full_text)) if full_text else 0
        sentence_count = max(sentence_count, 1) if full_text else 0

        avg_sentence_len = (
            round(word_count / sentence_count, 1) if sentence_count else 0
        )

        metrics = [
            Metric(
                name="word_count",
                display_name="Word Count",
                value=word_count,
                unit="words",
                category=MetricCategory.TEXT_STATISTICS,
            ),
            Metric(
                name="sentence_count",
                display_name="Sentence Count",
                value=sentence_count,
                unit="sentences",
                category=MetricCategory.TEXT_STATISTICS,
            ),
            Metric(
                name="paragraph_count",
                display_name="Paragraph Count",
                value=len(self._paragraphs),
                unit="paragraphs",
                category=MetricCategory.TEXT_STATISTICS,
            ),
            Metric(
                name="avg_sentence_length",
                display_name="Avg Sentence Length",
                value=avg_sentence_len,
                unit="words/sentence",
                category=MetricCategory.TEXT_STATISTICS,
                interpretation="15-20 words is considered ideal for readability",
            ),
            Metric(
                name="vocabulary_diversity",
                display_name="Vocabulary Diversity (TTR)",
                value=ttr,
                unit="ratio",
                category=MetricCategory.TEXT_STATISTICS,
                range_min=0,
                range_max=1,
                interpretation="Type-token ratio. Higher = more diverse vocabulary",
            ),
        ]
        return self._make_result(metrics)
