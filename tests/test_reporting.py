"""Tests for reporting formatters."""

from altscribe.analytics.base import AnalyzerResult, Metric, MetricCategory
from altscribe.checks.base import CheckResult, Issue, Severity
from altscribe.reporting.formatter import build_json_report, print_analytics_report


def _sample_check_result():
    return CheckResult(
        check_id="heading-hierarchy",
        check_name="Heading Hierarchy",
        issues=[
            Issue(
                check_id="heading-hierarchy",
                wcag_sc="1.3.1",
                severity=Severity.ERROR,
                message="Missing H1",
                location="Document",
            ),
        ],
    )


def _sample_analyzer_result():
    return AnalyzerResult(
        analyzer_id="readability",
        analyzer_name="Readability Metrics",
        category=MetricCategory.READABILITY,
        metrics=[
            Metric(
                name="flesch_kincaid_grade",
                display_name="Flesch-Kincaid Grade Level",
                value=8.2,
                unit="grade level",
                category=MetricCategory.READABILITY,
                interpretation="US school grade level",
            ),
        ],
    )


class TestJsonReport:
    def test_structure(self):
        report = build_json_report(
            [_sample_check_result()],
            [_sample_analyzer_result()],
        )
        assert "checks" in report
        assert "analytics" in report
        assert len(report["checks"]) == 1
        assert len(report["analytics"]) == 1

    def test_check_fields(self):
        report = build_json_report([_sample_check_result()], [])
        chk = report["checks"][0]
        assert chk["check_id"] == "heading-hierarchy"
        assert chk["issue_count"] == 1
        assert chk["issues"][0]["severity"] == "error"
        assert chk["issues"][0]["wcag_sc"] == "1.3.1"

    def test_analytics_fields(self):
        report = build_json_report([], [_sample_analyzer_result()])
        ar = report["analytics"][0]
        assert ar["analyzer_id"] == "readability"
        assert ar["metrics"][0]["name"] == "flesch_kincaid_grade"
        assert ar["metrics"][0]["value"] == 8.2

    def test_empty_report(self):
        report = build_json_report([], [])
        assert report["checks"] == []
        assert report["analytics"] == []


class TestTextReport:
    def test_prints_analytics(self, capsys):
        import sys

        print_analytics_report([_sample_analyzer_result()], file=sys.stdout)
        out = capsys.readouterr().out
        assert "Readability Metrics" in out
        assert "8.2" in out
        assert "grade level" in out
