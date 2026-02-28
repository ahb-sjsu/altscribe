"""Foundation types for the altscribe analytics system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, runtime_checkable

import panflute as pf


class MetricCategory(Enum):
    """Categories for organizing analytics metrics."""

    READABILITY = "readability"
    TEXT_STATISTICS = "text_statistics"
    WRITING_QUALITY = "writing_quality"
    CONTENT_STRUCTURE = "content_structure"
    ACCESSIBILITY_SCORE = "accessibility_score"


@dataclass
class Metric:
    """A single computed metric."""

    name: str
    display_name: str
    value: float | int | str
    unit: str = ""
    description: str = ""
    category: MetricCategory = MetricCategory.TEXT_STATISTICS
    range_min: float | None = None
    range_max: float | None = None
    interpretation: str = ""


@dataclass
class AnalyzerResult:
    """Aggregated result from a single analyzer."""

    analyzer_id: str
    analyzer_name: str
    category: MetricCategory
    metrics: list[Metric] = field(default_factory=list)

    def get_metric(self, name: str) -> Metric | None:
        """Look up a metric by its programmatic name."""
        for m in self.metrics:
            if m.name == name:
                return m
        return None


@runtime_checkable
class Analyzer(Protocol):
    """Protocol that all analytics analyzers implement."""

    analyzer_id: str
    analyzer_name: str
    category: MetricCategory
    element_types: tuple[type[pf.Element], ...]

    def analyze(self, elem: pf.Element, doc: pf.Doc) -> None: ...

    def finalize(self, doc: pf.Doc) -> AnalyzerResult: ...


class BaseAnalyzer:
    """Base class providing common boilerplate for analyzers."""

    analyzer_id: str = ""
    analyzer_name: str = ""
    category: MetricCategory = MetricCategory.TEXT_STATISTICS
    element_types: tuple[type[pf.Element], ...] = ()

    def _make_result(self, metrics: list[Metric]) -> AnalyzerResult:
        return AnalyzerResult(
            analyzer_id=self.analyzer_id,
            analyzer_name=self.analyzer_name,
            category=self.category,
            metrics=metrics,
        )

    def analyze(self, elem: pf.Element, doc: pf.Doc) -> None:
        raise NotImplementedError

    def finalize(self, doc: pf.Doc) -> AnalyzerResult:
        raise NotImplementedError
