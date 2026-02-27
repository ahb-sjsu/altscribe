"""Walk a pandoc AST and inject AI-generated alt-text for images."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import panflute as pf

from altscribe.vision import generate_alt_text


def _surrounding_text(elem: pf.Element, chars: int = 200) -> str:
    """Grab nearby plain text to give the model document context."""
    parts: list[str] = []
    parent = elem.parent
    if parent is None:
        return ""
    for child in parent.content:
        if isinstance(child, pf.Str):
            parts.append(child.text)
        elif isinstance(child, pf.Space):
            parts.append(" ")
    return "".join(parts)[:chars]


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
        Raw document text (markdown, html, rst, …).
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
    count = 0

    for elem in doc.walk():
        if not isinstance(elem, pf.Image):
            continue

        has_alt = pf.stringify(elem).strip() != ""
        if has_alt and not overwrite:
            continue

        src = elem.url
        if not src:
            continue

        context = _surrounding_text(elem)
        try:
            alt = generate_alt_text(src, api_key, base_dir, context=context)
        except Exception as exc:
            print(f"altscribe: warning: could not process {src}: {exc}", file=sys.stderr)
            continue

        elem.content = [pf.Str(alt)]
        count += 1

    print(f"altscribe: tagged {count} image(s)", file=sys.stderr)
    return pf.convert_text(
        doc,
        input_format="panflute",
        output_format=output_format,
    )
