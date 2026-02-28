"""Document language checker — WCAG SC 3.1.1."""

from __future__ import annotations

import panflute as pf

from altscribe.checks.base import BaseCheck, CheckResult


class DocumentLanguageCheck(BaseCheck):
    check_id = "document-language"
    check_name = "Document Language"
    wcag_sc = "3.1.1"
    element_types = (pf.Doc,)

    def __init__(self) -> None:
        super().__init__()
        self._missing_lang = False

    def check(self, elem: pf.Element, doc: pf.Doc) -> None:
        lang = doc.metadata.get("lang")
        if not lang:
            self._missing_lang = True
            self._add_issue(
                message="Document missing 'lang' metadata attribute",
                location="Document metadata",
            )

    def finalize(self, doc: pf.Doc, fix: bool) -> CheckResult:
        if fix and self._missing_lang:
            detected = self._detect_language(doc)
            doc.metadata["lang"] = pf.MetaString(detected)
            for issue in self._issues:
                if "lang" in issue.message and not issue.fixed:
                    issue.fixed = True
                    issue.fix_description = f"Set lang='{detected}'"
                    break

        return self._make_result()

    @staticmethod
    def _detect_language(doc: pf.Doc) -> str:
        """Detect document language from content."""
        text = pf.stringify(doc)[:1000]
        try:
            from langdetect import detect

            return detect(text)
        except (ImportError, Exception):
            return "en"
