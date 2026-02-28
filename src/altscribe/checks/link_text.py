"""Link text quality checker — WCAG SC 2.4.4."""

from __future__ import annotations

import re

import panflute as pf

from altscribe.checks.base import BaseCheck, CheckResult, Issue, Severity

_BAD_LINK_TEXT = {
    "click here",
    "here",
    "this link",
    "this",
    "link",
    "more",
    "read more",
    "learn more",
    "details",
    "info",
}

_URL_PATTERN = re.compile(r"^https?://\S+$")


class LinkTextCheck(BaseCheck):
    check_id = "link-text"
    check_name = "Link Text Quality"
    wcag_sc = "2.4.4"
    element_types = (pf.Link,)

    def __init__(self, api_key: str = "") -> None:
        super().__init__()
        self._api_key = api_key
        self._fixable: list[tuple[pf.Link, str, Issue]] = []
        self._seen_texts: dict[str, str] = {}

    def check(self, elem: pf.Element, doc: pf.Doc) -> None:
        assert isinstance(elem, pf.Link)
        link_text = pf.stringify(elem).strip()
        url = elem.url

        if not link_text:
            issue = self._add_issue(
                message=f"Link has no text: {url}",
                location=f"Link: {url[:60]}",
            )
            self._fixable.append((elem, "empty", issue))
            return

        if len(link_text) <= 2:
            issue = self._add_issue(
                message=f"Link text too short: '{link_text}' -> {url}",
                location=f"Link: '{link_text}'",
                severity=Severity.WARNING,
            )
            self._fixable.append((elem, "short", issue))
            return

        if link_text.lower().strip(".!") in _BAD_LINK_TEXT:
            issue = self._add_issue(
                message=f"Generic link text: '{link_text}' -> {url}",
                location=f"Link: '{link_text}'",
            )
            self._fixable.append((elem, "generic", issue))
            return

        if _URL_PATTERN.match(link_text):
            issue = self._add_issue(
                message=f"Bare URL as link text: {link_text[:60]}",
                location=f"Link: {link_text[:40]}",
            )
            self._fixable.append((elem, "bare_url", issue))
            return

        text_lower = link_text.lower()
        if text_lower in self._seen_texts:
            prev_url = self._seen_texts[text_lower]
            if prev_url != url:
                self._add_issue(
                    message=(
                        f"Duplicate link text '{link_text}' points to "
                        f"different URLs: {prev_url} and {url}"
                    ),
                    location=f"Link: '{link_text}'",
                    severity=Severity.WARNING,
                )
        else:
            self._seen_texts[text_lower] = url

    def finalize(self, doc: pf.Doc, fix: bool) -> CheckResult:
        if fix and self._fixable and self._api_key:
            self._fix_links()
        return self._make_result()

    def _fix_links(self) -> None:
        """Use Claude to generate descriptive link text in a single batch."""
        import anthropic

        from altscribe.vision import _parse_response

        client = anthropic.Anthropic(api_key=self._api_key)

        link_data = []
        for elem, reason, _ in self._fixable:
            context = _link_surrounding_text(elem)
            link_data.append(
                {
                    "url": elem.url,
                    "current_text": pf.stringify(elem).strip(),
                    "reason": reason,
                    "context": context,
                }
            )

        if not link_data:
            return

        prompt = (
            "For each link below, generate descriptive, accessible link text "
            "(WCAG 2.4.4). The link text should describe where the link goes "
            "or what it does. Keep it concise (2-8 words). "
            "Return a JSON array of strings, one per link, in the same order. "
            "Return ONLY the JSON array.\n\n"
        )
        for i, ld in enumerate(link_data):
            prompt += (
                f"{i + 1}. URL: {ld['url']}\n"
                f"   Current text: '{ld['current_text']}'\n"
                f"   Problem: {ld['reason']}\n"
                f"   Surrounding context: {ld['context']}\n\n"
            )

        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            replacements = _parse_response(response.content[0].text)

            for i, (elem, _, issue) in enumerate(self._fixable):
                if i < len(replacements):
                    new_text = replacements[i]
                    elem.content = [pf.Str(new_text)]
                    issue.fixed = True
                    issue.fix_description = f"Replaced with: '{new_text}'"
        except Exception:
            pass


def _link_surrounding_text(elem: pf.Element, chars: int = 200) -> str:
    """Get surrounding text for context."""
    parent = elem.parent
    if parent is not None and hasattr(parent, "content"):
        parts = []
        for child in parent.content:
            if isinstance(child, pf.Str):
                parts.append(child.text)
            elif isinstance(child, pf.Space):
                parts.append(" ")
        return "".join(parts)[:chars]
    return ""
