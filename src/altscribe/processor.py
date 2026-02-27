"""Walk a pandoc AST and inject AI-generated alt-text for images."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import panflute as pf

from altscribe.vision import AltTextResult, ImageType, generate_alt_text


def _surrounding_text(elem: pf.Element, chars: int = 300) -> str:
    """Grab nearby plain text and heading context for the model."""
    parts: list[str] = []

    # Walk up to find the nearest heading for section context
    current = elem.parent
    while current is not None:
        if isinstance(current, pf.Header):
            parts.insert(0, f"[Section: {pf.stringify(current)}] ")
            break
        current = getattr(current, "parent", None)

    # Get sibling text from the parent element
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
        # Walk up to the containing block element (usually a Para)
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


def _make_action(
    api_key: str,
    base_dir: Path,
    overwrite: bool,
    counter: list[int],
):
    """Return a panflute action callback that fills missing alt-text."""
    pending_long_desc: list[tuple[pf.Element, str]] = []

    def action(elem, doc):
        if not isinstance(elem, pf.Image):
            return None

        has_alt = pf.stringify(elem).strip() != ""
        if has_alt and not overwrite:
            return None

        src = elem.url
        if not src:
            return None

        is_functional, link_target = _is_in_link(elem)
        context = _surrounding_text(elem)

        try:
            result: AltTextResult = generate_alt_text(
                src,
                api_key,
                base_dir,
                context=context,
                is_functional=is_functional,
                link_target=link_target,
            )
        except Exception as exc:
            print(
                f"altscribe: warning: could not process {src}: {exc}",
                file=sys.stderr,
            )
            return None

        if result.image_type == ImageType.DECORATIVE:
            elem.content = []
            elem.title = ""
            elem.attributes["role"] = "presentation"
        else:
            elem.content = [pf.Str(result.alt_text)]

        if result.long_description:
            pending_long_desc.append((elem, result.long_description))

        counter[0] += 1
        return elem

    return action, pending_long_desc


_HTML_FORMATS = {"html", "html5", "html4"}


def _ensure_img_alt_attributes(html: str) -> str:
    """Add ``alt=""`` to any ``<img>`` tags missing the alt attribute.

    Pandoc may omit the alt attribute when Image content is empty, but
    WCAG requires ``alt=""`` on decorative images so screen readers skip them.
    """
    return re.sub(r"<img(?![^>]*\balt=)", '<img alt=""', html)


def process_document(
    source: str,
    input_format: str | None,
    output_format: str | None,
    api_key: str,
    base_dir: Path,
    *,
    overwrite: bool = False,
) -> str:
    """Parse *source* with pandoc, fill missing alt-text, and return the result.

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
    """
    input_format = input_format or "markdown"
    output_format = output_format or "markdown"

    doc = pf.convert_text(source, input_format=input_format, standalone=True)
    counter = [0]

    action, pending_long_desc = _make_action(api_key, base_dir, overwrite, counter)
    doc.walk(action)
    _insert_long_descriptions(doc, pending_long_desc)

    print(f"altscribe: tagged {counter[0]} image(s)", file=sys.stderr)
    result = pf.convert_text(
        doc,
        input_format="panflute",
        output_format=output_format,
    )

    if output_format in _HTML_FORMATS:
        result = _ensure_img_alt_attributes(result)

    return result
