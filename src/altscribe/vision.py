"""Send images to Claude for WCAG 2.1 AA compliant alt-text generation."""

from __future__ import annotations

import base64
import json
import mimetypes
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

import anthropic
import httpx


class ImageType(Enum):
    """W3C WAI image classification categories."""

    DECORATIVE = "decorative"
    INFORMATIVE = "informative"
    FUNCTIONAL = "functional"
    COMPLEX = "complex"
    TEXT = "text"


@dataclass
class AltTextResult:
    """Result of AI alt-text generation."""

    image_type: ImageType
    alt_text: str
    long_description: str | None = None


SYSTEM_PROMPT = """\
You are an accessibility expert generating alt text compliant with WCAG 2.1 \
Level AA (SC 1.1.1 Non-text Content, SC 1.4.5 Images of Text) for use by \
California State University faculty under ADA Title II, Section 508, and the \
CSU Accessible Technology Initiative.

Analyze the provided image and return a JSON object with these fields:

"image_type": one of "decorative", "informative", "functional", "complex", "text"
  - "decorative": purely visual flourish, spacer, border, or background with \
no informational value; or content fully described by adjacent text
  - "informative": photograph, illustration, or icon conveying information
  - "functional": image serving as a link or button (context will note this)
  - "complex": chart, graph, diagram, map, infographic, or data visualization
  - "text": image primarily containing readable text (e.g. scanned document, \
screenshot of text, stylized heading)

"alt_text": the appropriate alt-text string
  - decorative: exactly ""
  - informative: concise description of what the image conveys, under 125 characters
  - functional: describe the ACTION or DESTINATION, not appearance (e.g. \
"Search", "Download annual report PDF", "Navigate to homepage")
  - complex: short label identifying the image type and subject \
(e.g. "Bar chart comparing Q1 through Q4 revenue by region")
  - text: verbatim transcription of ALL text visible in the image

"long_description": (required for "complex", null for all others)
  - Structured prose describing ALL data, relationships, trends, and takeaways
  - Include specific values, labels, axis titles, and legends
  - Use clear language a screen-reader user can follow without seeing the image

Rules:
- NEVER begin with "image of", "picture of", "photo of", "graphic of"
- Describe content and function, not visual style
- For informative images, focus on the information the image communicates in \
its document context, not exhaustive visual detail
- Return ONLY the JSON object with no markdown fencing or extra text\
"""


MIME_TYPES: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}


def _resolve_image(src: str, base_dir: Path) -> tuple[str, bytes]:
    """Return (media_type, raw_bytes) for a local or remote image."""
    parsed = urlparse(src)

    if parsed.scheme in ("http", "https"):
        resp = httpx.get(src, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "image/png").split(";")[0]
        return content_type, resp.content

    path = Path(src) if Path(src).is_absolute() else base_dir / src
    suffix = path.suffix.lower()
    media_type = (
        MIME_TYPES.get(suffix) or mimetypes.guess_type(str(path))[0] or "image/png"
    )
    return media_type, path.read_bytes()


def _parse_response(raw: str) -> dict:
    """Parse the JSON response, stripping markdown fences if present."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
    return json.loads(text)


def generate_alt_text(
    src: str,
    api_key: str,
    base_dir: Path,
    context: str = "",
    is_functional: bool = False,
    link_target: str = "",
) -> AltTextResult:
    """Classify image and produce WCAG 2.1 AA compliant alt-text."""
    media_type, image_bytes = _resolve_image(src, base_dir)
    b64 = base64.standard_b64encode(image_bytes).decode()

    user_parts: list[str] = ["Analyze this image and generate accessible alt text."]
    if is_functional:
        user_parts.append(
            f"This image is used INSIDE A LINK/BUTTON. "
            f"Link destination: {link_target or 'unknown'}. "
            f"Describe the action or destination, not the image appearance."
        )
    if context:
        user_parts.append(f"Surrounding document context: {context}")
    user_msg = " ".join(user_parts)

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": user_msg},
                ],
            },
        ],
    )

    data = _parse_response(response.content[0].text)
    image_type = ImageType(data["image_type"])

    return AltTextResult(
        image_type=image_type,
        alt_text=data.get("alt_text", ""),
        long_description=(
            data.get("long_description") if image_type == ImageType.COMPLEX else None
        ),
    )
