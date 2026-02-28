"""Tests for accessibility score aggregator."""

from altscribe.analytics.accessibility_score import AccessibilityScoreAggregator
from altscribe.analytics.base import AnalyzerResult, Metric, MetricCategory
from altscribe.checks.base import CheckResult, Issue, Severity


def _check_result(check_id: str, issues: list[Issue] | None = None) -> CheckResult:
    return CheckResult(
        check_id=check_id,
        check_name=check_id,
        issues=issues or [],
    )


def _readability_result(grade: float) -> AnalyzerResult:
    return AnalyzerResult(
        analyzer_id="readability",
        analyzer_name="Readability",
        category=MetricCategory.READABILITY,
        metrics=[
            Metric(
                name="flesch_kincaid_grade",
                display_name="FK Grade",
                value=grade,
                category=MetricCategory.READABILITY,
            ),
        ],
    )


class TestAccessibilityScore:
    def test_perfect_score(self):
        checks = [
            _check_result("image-alt-text"),
            _check_result("heading-hierarchy"),
            _check_result("link-text"),
        ]
        analyzers = [_readability_result(5.0)]
        agg = AccessibilityScoreAggregator()
        result = agg.compute(checks, analyzers)
        score = result.get_metric("accessibility_score")
        assert score is not None
        assert score.value == 100.0

    def test_issues_reduce_score(self):
        checks = [
            _check_result(
                "heading-hierarchy",
                issues=[
                    Issue(
                        check_id="heading-hierarchy",
                        wcag_sc="1.3.1",
                        severity=Severity.ERROR,
                        message="Missing H1",
                        location="Document",
                    ),
                ],
            ),
        ]
        agg = AccessibilityScoreAggregator()
        result = agg.compute(checks, [])
        score = result.get_metric("accessibility_score")
        assert score is not None
        assert score.value < 100.0

    def test_fixed_issues_dont_penalize(self):
        checks = [
            _check_result(
                "heading-hierarchy",
                issues=[
                    Issue(
                        check_id="heading-hierarchy",
                        wcag_sc="1.3.1",
                        severity=Severity.ERROR,
                        message="Skipped level",
                        location="H3",
                        fixed=True,
                    ),
                ],
            ),
        ]
        agg = AccessibilityScoreAggregator()
        result = agg.compute(checks, [])
        score = result.get_metric("accessibility_score")
        assert score is not None
        assert score.value == 100.0

    def test_hard_readability_reduces_score(self):
        checks = [_check_result("heading-hierarchy")]
        analyzers_easy = [_readability_result(5.0)]
        analyzers_hard = [_readability_result(16.0)]

        agg = AccessibilityScoreAggregator()
        easy = agg.compute(checks, analyzers_easy).get_metric("accessibility_score")
        hard = agg.compute(checks, analyzers_hard).get_metric("accessibility_score")
        assert easy is not None and hard is not None
        assert easy.value > hard.value

    def test_score_in_range(self):
        checks = [
            _check_result(
                "image-alt-text",
                issues=[
                    Issue(
                        check_id="image-alt-text",
                        wcag_sc="1.1.1",
                        severity=Severity.ERROR,
                        message="Missing alt",
                        location="img",
                    )
                    for _ in range(50)
                ],
            ),
        ]
        agg = AccessibilityScoreAggregator()
        result = agg.compute(checks, [])
        score = result.get_metric("accessibility_score")
        assert score is not None
        assert 0 <= score.value <= 100
