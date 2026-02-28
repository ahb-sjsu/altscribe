"""Image alt-text checker — WCAG SC 1.1.1, 1.4.5."""

from __future__ import annotations

import sys
from pathlib import Path

import panflute as pf

from altscribe.checks.base import BaseCheck, CheckResult, Issue
from altscribe.vision import AltTextResult, ImageType, generate_alt_text


class ImageAltTextCheck(BaseCheck):
    check_id = "image-alt-text"
    check_name = "Image Alt Text"
    wcag_sc = "1.1.1"
    element_types = (pf.Image,)

    def __init__(
        self,
        api_key: str,
        base_dir: Path,
        overwrite: bool = False,
    ) -> None:
        super().__init__()
        self._api_key = api_key
        self._base_dir = base_dir
        self._overwrite = overwrite
        self._pending: list[tuple[pf.Image, Issue]] = []
        self._pending_long_desc: list[tuple[pf.Image, str]] = []

    def check(self, elem: pf.Element, doc: pf.Doc) -> None:
        assert isinstance(elem, pf.Image)

        has_alt = pf.stringify(elem).strip() != ""
        if has_alt and not self._overwrite:
            return

        src = elem.url
        if not src:
            return

        issue = self._add_issue(
            message=f"Image '{src}' missing alt text",
            location=f"Image: {src}",
        )
        self._pending.append((elem, issue))

    def finalize(self, doc: pf.Doc, fix: bool) -> CheckResult:
        if fix:
            for elem, issue in self._pending:
                self._fix_image(elem, issue)
            _insert_long_descriptions(doc, self._pending_long_desc)
        return self._make_result()

    def _fix_image(self, elem: pf.Image, issue: Issue) -> None:
        is_functional, link_target = _is_in_link(elem)
        context = _surrounding_text(elem)

        try:
            result: AltTextResult = generate_alt_text(
                elem.url,
                self._api_key,
                self._base_dir,
                context=context,
                is_functional=is_functional,
                link_target=link_target,
            )
        except Exception as exc:
            print(
                f"altscribe: warning: could not process {elem.url}: {exc}",
                file=sys.stderr,
            )
            return

        if result.image_type == ImageType.DECORATIVE:
            elem.content = []
            elem.title = ""
            elem.attributes["role"] = "presentation"
            issue.fix_description = "Marked as decorative (alt='')"
        else:
            elem.content = [pf.Str(result.alt_text)]
            issue.fix_description = f"Set alt text: {result.alt_text[:60]}"

        if result.long_description:
            self._pending_long_desc.append((elem, result.long_description))

        issue.fixed = True


def _surrounding_text(elem: pf.Element, chars: int = 300) -> str:
    """Grab nearby plain text and heading context for the model."""
    parts: list[str] = []

    current = elem.parent
    while current is not None:
        if isinstance(current, pf.Header):
            parts.insert(0, f"[Section: {pf.stringify(current)}] ")
            break
        current = getattr(current, "parent", None)

    parent = elem.parent
    if parent is not None and hasattr(parent, "content"):
        for child in parent.content:
            if isinstance(child, pf.Str):
                parts.append(child.text)
            elif isinstance(child, pf.Space):
                parts.append(" ")
    return "".join(parts)[:chars]


def _is_in_link(elem: pf.Element) -> tuple[bool, str]:
    """Check if the image is inside a link element."""
    parent = elem.parent
    while parent is not None:
        if isinstance(parent, pf.Link):
            return True, parent.url
        parent = getattr(parent, "parent", None)
    return False, ""


def _insert_long_descriptions(
    doc: pf.Doc,
    pending: list[tuple[pf.Element, str]],
) -> None:
    """Insert long descriptions after paragraphs containing complex images."""
    for img, desc in pending:
        parent = img.parent
        while parent is not None and not isinstance(parent, (pf.Para, pf.Plain)):
            parent = getattr(parent, "parent", None)
        if parent is None:
            continue

        grandparent = parent.parent
        if grandparent is None or not hasattr(grandparent, "content"):
            continue

        idx = None
        for i, child in enumerate(grandparent.content):
            if child is parent:
                idx = i
                break
        if idx is None:
            continue

        desc_block = pf.Div(
            pf.Para(pf.Strong(pf.Str("Image description: ")), pf.Str(desc)),
            classes=["altscribe-long-desc"],
            attributes={"role": "note"},
        )
        grandparent.content.insert(idx + 1, desc_block)
