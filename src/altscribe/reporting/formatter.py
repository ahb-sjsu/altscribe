"""Report formatters — JSON and human-readable output."""

from __future__ import annotations

import sys

from altscribe.analytics.base import AnalyzerResult
from altscribe.checks.base import CheckResult


def build_json_report(
    check_results: list[CheckResult],
    analyzer_results: list[AnalyzerResult],
) -> dict:
    """Build a structured JSON report from check and analytics results."""
    return {
        "checks": [
            {
                "check_id": cr.check_id,
                "check_name": cr.check_name,
                "issue_count": len(cr.issues),
                "error_count": cr.error_count,
                "fixed_count": cr.fixed_count,
                "issues": [
                    {
                        "severity": i.severity.value,
                        "message": i.message,
                        "location": i.location,
                        "wcag_sc": i.wcag_sc,
                        "fixed": i.fixed,
                        "fix_description": i.fix_description,
                    }
                    for i in cr.issues
                ],
            }
            for cr in check_results
        ],
        "analytics": [
            {
                "analyzer_id": ar.analyzer_id,
                "analyzer_name": ar.analyzer_name,
                "category": ar.category.value,
                "metrics": [
                    {
                        "name": m.name,
                        "display_name": m.display_name,
                        "value": m.value,
                        "unit": m.unit,
                        "interpretation": m.interpretation,
                    }
                    for m in ar.metrics
                ],
            }
            for ar in analyzer_results
        ],
    }


def print_analytics_report(
    analyzer_results: list[AnalyzerResult],
    file=sys.stderr,
) -> None:
    """Print a human-readable analytics summary."""
    for ar in analyzer_results:
        print(f"\n  {ar.analyzer_name} ({ar.analyzer_id}):", file=file)
        for m in ar.metrics:
            unit_str = f" {m.unit}" if m.unit else ""
            print(f"    {m.display_name}: {m.value}{unit_str}", file=file)
            if m.interpretation:
                print(f"      ({m.interpretation})", file=file)
