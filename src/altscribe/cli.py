"""CLI entry-point for altscribe."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from altscribe.processor import process_document


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", "output_file", type=click.Path(path_type=Path), default=None, help="Output file path (default: stdout).")
@click.option("-f", "--from", "input_format", default=None, help="Pandoc input format (default: auto-detect).")
@click.option("-t", "--to", "output_format", default=None, help="Pandoc output format (default: markdown).")
@click.option("--api-key", envvar="ANTHROPIC_API_KEY", required=True, help="Anthropic API key (or set ANTHROPIC_API_KEY).")
@click.option("--overwrite", is_flag=True, default=False, help="Regenerate alt-text even for images that already have it.")
def main(
    input_file: Path,
    output_file: Path | None,
    input_format: str | None,
    output_format: str | None,
    api_key: str,
    overwrite: bool,
) -> None:
    """Add AI-generated alt-text to every image in a document.

    Reads INPUT_FILE, sends each image to Claude for an accessible description,
    and writes the result with alt-text injected.
    """
    source = input_file.read_text(encoding="utf-8")
    base_dir = input_file.parent.resolve()

    result = process_document(
        source,
        input_format=input_format,
        output_format=output_format,
        api_key=api_key,
        base_dir=base_dir,
        overwrite=overwrite,
    )

    if output_file:
        output_file.write_text(result, encoding="utf-8")
        click.echo(f"altscribe: wrote {output_file}", err=True)
    else:
        click.echo(result)
