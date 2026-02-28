"""Writing quality analyzer — passive voice, complex sentences."""

from __future__ import annotations

import re

import panflute as pf

from altscribe.analytics.base import (
    AnalyzerResult,
    BaseAnalyzer,
    Metric,
    MetricCategory,
)

_PASSIVE_REGULAR = re.compile(
    r"\b(?:am|is|are|was|were|been|being|be)\b\s+\w+ed\b",
    re.IGNORECASE,
)
_PASSIVE_IRREGULAR = re.compile(
    r"\b(?:am|is|are|was|were|been|being|be)\b\s+"
    r"(?:made|done|given|taken|seen|known|found|told|shown|written|built|"
    r"held|kept|brought|bought|taught|thought|caught|sent|left|run|set|"
    r"put|cut|read|paid|said|lost|spent|grown|drawn|broken|chosen|"
    r"driven|eaten|fallen|forgotten|frozen|gotten|hidden|ridden|risen|"
    r"shaken|spoken|stolen|sworn|torn|woken|worn)\b",
    re.IGNORECASE,
)

_CLAUSE_MARKERS = re.compile(
    r"\b(?:which|that|because|although|while|whereas|if|when|where|who|whom)\b",
    re.IGNORECASE,
)


def _is_passive(sentence: str) -> bool:
    return bool(
        _PASSIVE_REGULAR.search(sentence) or _PASSIVE_IRREGULAR.search(sentence)
    )


def _is_complex(sentence: str, word_threshold: int = 25) -> bool:
    if len(sentence.split()) >= word_threshold:
        return True
    return len(_CLAUSE_MARKERS.findall(sentence)) >= 3


class WritingQualityAnalyzer(BaseAnalyzer):
    analyzer_id = "writing-quality"
    analyzer_name = "Writing Quality"
    category = MetricCategory.WRITING_QUALITY
    element_types = (pf.Para, pf.Plain)

    def __init__(self) -> None:
        self._sentences: list[str] = []

    def analyze(self, elem: pf.Element, doc: pf.Doc) -> None:
        text = pf.stringify(elem).strip()
        if not text:
            return
        for sent in re.split(r"(?<=[.!?])\s+", text):
            sent = sent.strip()
            if sent:
                self._sentences.append(sent)

    def finalize(self, doc: pf.Doc) -> AnalyzerResult:
        total = len(self._sentences)
        if total == 0:
            return self._make_result([])

        passive_count = sum(1 for s in self._sentences if _is_passive(s))
        complex_count = sum(1 for s in self._sentences if _is_complex(s))

        metrics = [
            Metric(
                name="passive_voice_pct",
                display_name="Passive Voice",
                value=round(passive_count / total * 100, 1),
                unit="%",
                category=MetricCategory.WRITING_QUALITY,
                range_min=0,
                range_max=100,
                interpretation="Below 10% is ideal for accessibility",
            ),
            Metric(
                name="complex_sentence_pct",
                display_name="Complex Sentences",
                value=round(complex_count / total * 100, 1),
                unit="%",
                category=MetricCategory.WRITING_QUALITY,
                range_min=0,
                range_max=100,
                interpretation="Sentences with 3+ clauses or 25+ words",
            ),
            Metric(
                name="sentence_count_analyzed",
                display_name="Sentences Analyzed",
                value=total,
                unit="sentences",
                category=MetricCategory.WRITING_QUALITY,
            ),
        ]
        return self._make_result(metrics)
