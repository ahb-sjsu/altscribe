"""Accessibility score aggregator — composite 0-100 score."""

from __future__ import annotations

from altscribe.analytics.base import AnalyzerResult, Metric, MetricCategory
from altscribe.checks.base import CheckResult


class AccessibilityScoreAggregator:
    """Computes a composite 0-100 accessibility score from check + analytics results."""

    # Weights per check category (total = 100 when combined with readability).
    CHECK_WEIGHTS: dict[str, float] = {
        "image-alt-text": 20,
        "heading-hierarchy": 15,
        "link-text": 15,
        "table-accessibility": 10,
        "document-language": 10,
        "list-structure": 10,
        "color-contrast": 10,
    }
    READABILITY_WEIGHT: float = 10

    def compute(
        self,
        check_results: list[CheckResult],
        analyzer_results: list[AnalyzerResult],
    ) -> AnalyzerResult:
        """Compute the composite score.

        Each check starts at full weight, loses points per unfixed issue.
        Readability bonus: Flesch-Kincaid grade <= 8 gets full points.
        """
        score = 0.0

        # Score from checks
        active_weight = 0.0
        for cr in check_results:
            weight = self.CHECK_WEIGHTS.get(cr.check_id, 5)
            active_weight += weight
            if not cr.issues:
                score += weight
            else:
                unfixed = cr.error_count - cr.fixed_count
                penalty = min(unfixed * (weight / 5), weight)
                score += max(weight - penalty, 0)

        # Readability bonus
        fk_value = None
        for ar in analyzer_results:
            fk = ar.get_metric("flesch_kincaid_grade")
            if fk is not None:
                fk_value = float(fk.value)
                break

        if fk_value is not None:
            active_weight += self.READABILITY_WEIGHT
            if fk_value <= 8:
                score += self.READABILITY_WEIGHT
            elif fk_value <= 16:
                score += self.READABILITY_WEIGHT * (1 - (fk_value - 8) / 8)

        # Normalize to 0-100 based on active weights
        if active_weight > 0:
            final_score = round(score / active_weight * 100, 1)
        else:
            final_score = 100.0

        final_score = min(max(final_score, 0), 100)

        return AnalyzerResult(
            analyzer_id="accessibility-score",
            analyzer_name="Accessibility Score",
            category=MetricCategory.ACCESSIBILITY_SCORE,
            metrics=[
                Metric(
                    name="accessibility_score",
                    display_name="Overall Accessibility Score",
                    value=final_score,
                    unit="/ 100",
                    range_min=0,
                    range_max=100,
                    category=MetricCategory.ACCESSIBILITY_SCORE,
                    interpretation="Composite score across all checks and readability",
                ),
            ],
        )
