"""Send images to Claude for accessible alt-text generation."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from urllib.parse import urlparse

import anthropic
import httpx

SYSTEM_PROMPT = (
    "You are an accessibility expert. Given an image, produce a concise, "
    "descriptive alt-text string suitable for a screen reader. Follow WCAG 2.2 "
    "guidelines: be concise (generally under 125 characters), describe the "
    "content and function of the image, and avoid phrases like 'image of' or "
    "'picture of'. Return ONLY the alt-text string, with no quotes or extra "
    "formatting."
)

MIME_TYPES: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
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
    media_type = MIME_TYPES.get(suffix) or mimetypes.guess_type(str(path))[0] or "image/png"
    return media_type, path.read_bytes()


def generate_alt_text(
    src: str,
    api_key: str,
    base_dir: Path,
    context: str = "",
) -> str:
    """Use Claude's vision to produce alt-text for *src*."""
    media_type, image_bytes = _resolve_image(src, base_dir)
    b64 = base64.standard_b64encode(image_bytes).decode()

    user_msg = "Describe this image for use as alt-text."
    if context:
        user_msg += f" Surrounding document context: {context}"

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
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
            }
        ],
    )
    return response.content[0].text.strip()
