"""Heading hierarchy checker — WCAG SC 1.3.1, 2.4.6."""

from __future__ import annotations

import panflute as pf

from altscribe.checks.base import BaseCheck, CheckResult, Severity


class HeadingHierarchyCheck(BaseCheck):
    check_id = "heading-hierarchy"
    check_name = "Heading Hierarchy"
    wcag_sc = "1.3.1"
    element_types = (pf.Header, pf.Para)

    def __init__(self) -> None:
        super().__init__()
        self._headers: list[tuple[pf.Header, int]] = []
        self._fake_headings: list[pf.Para] = []

    def check(self, elem: pf.Element, doc: pf.Doc) -> None:
        if isinstance(elem, pf.Header):
            self._headers.append((elem, elem.level))
            if not pf.stringify(elem).strip():
                self._add_issue(
                    message="Empty heading",
                    location=f"H{elem.level}",
                )
        elif isinstance(elem, pf.Para) and self._is_fake_heading(elem):
            self._fake_headings.append(elem)
            text_preview = pf.stringify(elem)[:50]
            self._add_issue(
                message=f"Fake heading (bold-only paragraph): '{text_preview}'",
                location="Para (bold-only)",
                severity=Severity.WARNING,
            )

    def finalize(self, doc: pf.Doc, fix: bool) -> CheckResult:
        levels = [lvl for _, lvl in self._headers]
        if levels and 1 not in levels:
            self._add_issue(
                message="Document has no H1 heading",
                location="Document",
            )

        skip_fixes: list[tuple[pf.Header, int, int]] = []
        for i in range(1, len(self._headers)):
            prev_level = self._headers[i - 1][1]
            curr_elem, curr_level = self._headers[i]
            if curr_level > prev_level + 1:
                expected = prev_level + 1
                heading_text = pf.stringify(curr_elem)[:40]
                self._add_issue(
                    message=(
                        f"Skipped heading level: H{prev_level} -> "
                        f"H{curr_level} (expected H{expected})"
                    ),
                    location=f"H{curr_level}: '{heading_text}'",
                )
                skip_fixes.append((curr_elem, curr_level, expected))

        if fix:
            for elem, old_level, new_level in skip_fixes:
                elem.level = new_level
                for j, (h, _) in enumerate(self._headers):
                    if h is elem:
                        self._headers[j] = (h, new_level)
                        break
                for issue in self._issues:
                    if (
                        f"H{old_level}" in issue.location
                        and "Skipped" in issue.message
                        and not issue.fixed
                    ):
                        issue.fixed = True
                        issue.fix_description = f"Re-leveled to H{new_level}"
                        break

            for para in self._fake_headings:
                self._promote_fake_heading(para)

        return self._make_result()

    @staticmethod
    def _is_fake_heading(para: pf.Para) -> bool:
        """Bold-only or emph-only paragraphs that look like headings."""
        meaningful = [
            c for c in para.content if not isinstance(c, (pf.Space, pf.SoftBreak))
        ]
        if not meaningful:
            return False
        return all(isinstance(c, (pf.Strong, pf.Emph)) for c in meaningful)

    def _promote_fake_heading(self, para: pf.Para) -> None:
        """Replace a fake-heading Para with a proper Header."""
        last_level = self._headers[-1][1] if self._headers else 0
        new_level = min(last_level + 1, 6) if last_level else 2

        new_content: list[pf.Element] = []
        for child in para.content:
            if isinstance(child, (pf.Strong, pf.Emph)):
                new_content.extend(child.content)
            else:
                new_content.append(child)

        header = pf.Header(*new_content, level=new_level)

        parent = para.parent
        if parent is not None and hasattr(parent, "content"):
            for i, child in enumerate(parent.content):
                if child is para:
                    parent.content[i] = header
                    break

        self._headers.append((header, new_level))
        for issue in self._issues:
            if "Fake heading" in issue.message and not issue.fixed:
                issue.fixed = True
                issue.fix_description = f"Promoted to H{new_level}"
                break
