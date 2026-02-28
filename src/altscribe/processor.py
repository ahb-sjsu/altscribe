"""Document processor — walks pandoc AST and dispatches to checkers + analyzers."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import panflute as pf

from altscribe.analytics.base import AnalyzerResult, BaseAnalyzer
from altscribe.analytics.registry import get_enabled_analyzers
from altscribe.checks.base import Check, CheckResult
from altscribe.checks.registry import get_enabled_checks


def _build_dispatch_map(
    checks: list[Check],
    analyzers: list[BaseAnalyzer] | None = None,
) -> dict[type[pf.Element], list[Any]]:
    """Map element types to the checkers/analyzers that want them."""
    dispatch: dict[type[pf.Element], list[Any]] = defaultdict(list)
    for chk in checks:
        for etype in chk.element_types:
            if etype is not pf.Doc:
                dispatch[etype].append(chk)
    for analyzer in analyzers or []:
        for etype in analyzer.element_types:
            if etype is not pf.Doc:
                dispatch[etype].append(analyzer)
    return dict(dispatch)


def _make_action(
    dispatch_map: dict[type[pf.Element], list[Any]],
):
    """Return a panflute action that dispatches to all registered handlers."""

    def action(elem: pf.Element, doc: pf.Doc):
        for etype, handlers in dispatch_map.items():
            if isinstance(elem, etype):
                for handler in handlers:
                    if isinstance(handler, BaseAnalyzer):
                        handler.analyze(elem, doc)
                    else:
                        handler.check(elem, doc)
        return None

    return action


_HTML_FORMATS = {"html", "html5", "html4"}


def _ensure_img_alt_attributes(html: str) -> str:
    """Add ``alt=""`` to any ``<img>`` tags missing the alt attribute."""
    return re.sub(r"<img(?![^>]*\balt=)", '<img alt=""', html)


def _print_report(results: list[CheckResult], file=sys.stderr) -> int:
    """Print a summary report to stderr. Return total issue count."""
    total_issues = 0
    total_fixed = 0
    for r in results:
        if not r.issues:
            continue
        print(f"\n  {r.check_name} ({r.check_id}):", file=file)
        for issue in r.issues:
            status = " [FIXED]" if issue.fixed else ""
            print(
                f"    {issue.severity.value.upper()}: {issue.message} "
                f"({issue.location}){status}",
                file=file,
            )
        total_issues += len(r.issues)
        total_fixed += r.fixed_count

    if total_issues:
        print(
            f"\naltscribe: {total_issues} issue(s) found, " f"{total_fixed} fixed",
            file=file,
        )
    else:
        print("altscribe: no accessibility issues found", file=file)

    return total_issues


def process_document(
    source: str,
    input_format: str | None,
    output_format: str | None,
    api_key: str,
    base_dir: Path,
    *,
    overwrite: bool = False,
    fix: bool = True,
    enabled_checks: list[str] | None = None,
    disabled_checks: list[str] | None = None,
    run_analytics: bool = False,
    enabled_analyzers: list[str] | None = None,
    disabled_analyzers: list[str] | None = None,
) -> tuple[str, list[CheckResult], list[AnalyzerResult]]:
    """Parse source, run accessibility checks/analytics, and return results.

    Parameters
    ----------
    source:
        Raw document text (markdown, html, rst, ...).
    input_format:
        Pandoc input format.  ``None`` means pandoc will guess.
    output_format:
        Pandoc output format.  ``None`` defaults to ``markdown``.
    api_key:
        Anthropic API key.
    base_dir:
        Directory used to resolve relative image paths.
    overwrite:
        If *True*, regenerate alt-text even for images that already have it.
    fix:
        If *True* (default), apply fixes.  If *False*, report only.
    enabled_checks:
        If set, only run these check IDs.  None means all.
    disabled_checks:
        Check IDs to skip.  Applied after enabled_checks.
    run_analytics:
        If *True*, run document analytics and return results.
    enabled_analyzers:
        If set, only run these analyzer IDs.  None means all.
    disabled_analyzers:
        Analyzer IDs to skip.

    Returns
    -------
    (output_text, list_of_CheckResult, list_of_AnalyzerResult)
    """
    input_format = input_format or "markdown"
    output_format = output_format or "markdown"

    doc = pf.convert_text(source, input_format=input_format, standalone=True)

    checks = get_enabled_checks(
        api_key=api_key,
        base_dir=base_dir,
        overwrite=overwrite,
        enabled=enabled_checks,
        disabled=disabled_checks,
        raw_html=source if input_format in _HTML_FORMATS else "",
    )

    analyzers: list[BaseAnalyzer] = []
    if run_analytics:
        analyzers = get_enabled_analyzers(
            enabled=enabled_analyzers,
            disabled=disabled_analyzers,
        )

    # Pre-walk pass for Doc-level checkers (e.g. document language)
    for chk in checks:
        if pf.Doc in chk.element_types:
            chk.check(doc, doc)
    for analyzer in analyzers:
        if pf.Doc in analyzer.element_types:
            analyzer.analyze(doc, doc)

    dispatch_map = _build_dispatch_map(checks, analyzers)
    action = _make_action(dispatch_map)
    doc.walk(action)

    # Finalize phase: apply fixes and collect results
    results: list[CheckResult] = []
    for chk in checks:
        result = chk.finalize(doc, fix=fix)
        results.append(result)

    # Finalize analyzers (read-only, after fixes applied)
    analyzer_results: list[AnalyzerResult] = []
    for analyzer in analyzers:
        ar = analyzer.finalize(doc)
        analyzer_results.append(ar)

    # Compute accessibility score (consumes both check + analyzer results)
    if run_analytics:
        from altscribe.analytics.accessibility_score import (
            AccessibilityScoreAggregator,
        )

        score_result = AccessibilityScoreAggregator().compute(results, analyzer_results)
        analyzer_results.append(score_result)

    _print_report(results)

    output = pf.convert_text(
        doc,
        input_format="panflute",
        output_format=output_format,
    )

    if output_format in _HTML_FORMATS:
        output = _ensure_img_alt_attributes(output)

    return output, results, analyzer_results
