"""Table accessibility checker — WCAG SC 1.3.1."""

from __future__ import annotations

import panflute as pf

from altscribe.checks.base import BaseCheck, CheckResult, Issue


class TableAccessibilityCheck(BaseCheck):
    check_id = "table-accessibility"
    check_name = "Table Accessibility"
    wcag_sc = "1.3.1"
    element_types = (pf.Table,)

    def __init__(self, api_key: str = "") -> None:
        super().__init__()
        self._api_key = api_key
        self._tables_needing_caption: list[tuple[pf.Table, Issue]] = []

    def check(self, elem: pf.Element, doc: pf.Doc) -> None:
        assert isinstance(elem, pf.Table)

        caption = elem.caption
        caption_text = ""
        if caption is not None:
            caption_text = pf.stringify(caption).strip()

        if not caption_text:
            issue = self._add_issue(
                message="Table missing caption",
                location="Table",
            )
            self._tables_needing_caption.append((elem, issue))

        head = elem.head
        if head is not None:
            head_rows = list(head.content) if hasattr(head, "content") else []
            has_content = any(pf.stringify(row).strip() for row in head_rows)
            if not has_content:
                self._add_issue(
                    message="Table has no header row",
                    location="Table",
                )

    def finalize(self, doc: pf.Doc, fix: bool) -> CheckResult:
        if fix and self._api_key:
            self._fix_captions()
        return self._make_result()

    def _fix_captions(self) -> None:
        """Use Claude to generate captions for tables."""
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)

        for table, issue in self._tables_needing_caption:
            table_text = pf.stringify(table)[:500]
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=256,
                    messages=[
                        {
                            "role": "user",
                            "content": (
                                "Generate a concise, descriptive caption "
                                "for this table (one sentence, no quotes, "
                                "suitable for a <caption> element):\n\n"
                                f"{table_text}"
                            ),
                        }
                    ],
                )
                caption_text = response.content[0].text.strip().strip('"').strip("'")
                table.caption = pf.Caption(pf.Para(pf.Str(caption_text)))
                issue.fixed = True
                issue.fix_description = f"Added caption: '{caption_text[:50]}'"
            except Exception:
                pass
