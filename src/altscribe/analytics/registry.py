"""Analytics registry — lists all analyzer classes and instantiates them."""

from __future__ import annotations

from altscribe.analytics.base import BaseAnalyzer
from altscribe.analytics.content_structure import ContentStructureAnalyzer
from altscribe.analytics.readability import ReadabilityAnalyzer
from altscribe.analytics.text_statistics import TextStatisticsAnalyzer
from altscribe.analytics.writing_quality import WritingQualityAnalyzer

ALL_ANALYZER_CLASSES: list[type[BaseAnalyzer]] = [
    TextStatisticsAnalyzer,
    ReadabilityAnalyzer,
    WritingQualityAnalyzer,
    ContentStructureAnalyzer,
]


def get_enabled_analyzers(
    *,
    enabled: list[str] | None = None,
    disabled: list[str] | None = None,
) -> list[BaseAnalyzer]:
    """Instantiate and return the requested analyzers."""
    disabled_set = set(disabled or [])
    classes = list(ALL_ANALYZER_CLASSES)

    if enabled is not None:
        enabled_set = set(enabled)
        classes = [c for c in classes if c.analyzer_id in enabled_set]

    classes = [c for c in classes if c.analyzer_id not in disabled_set]
    return [cls() for cls in classes]
