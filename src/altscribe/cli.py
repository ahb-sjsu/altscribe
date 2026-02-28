"""CLI entry-point for altscribe."""

from __future__ import annotations

from pathlib import Path

import click

from altscribe.processor import process_document


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o",
    "--output",
    "output_file",
    type=click.Path(path_type=Path),
    default=None,
    help="Output file path (default: stdout).",
)
@click.option(
    "-f",
    "--from",
    "input_format",
    default=None,
    help="Pandoc input format (default: auto-detect).",
)
@click.option(
    "-t",
    "--to",
    "output_format",
    default=None,
    help="Pandoc output format (default: markdown).",
)
@click.option(
    "--api-key",
    envvar="ANTHROPIC_API_KEY",
    default=None,
    help="Anthropic API key (or set ANTHROPIC_API_KEY). "
    "Required for fix mode; optional for --check.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    default=False,
    help="Regenerate alt-text even for images that already have it.",
)
@click.option(
    "--check",
    "check_only",
    is_flag=True,
    default=False,
    help="Report accessibility issues without fixing them.",
)
@click.option(
    "--enable",
    "enable_checks",
    multiple=True,
    help="Only run these checks (by ID). Repeatable.",
)
@click.option(
    "--disable",
    "disable_checks",
    multiple=True,
    help="Skip these checks (by ID). Repeatable.",
)
def main(
    input_file: Path,
    output_file: Path | None,
    input_format: str | None,
    output_format: str | None,
    api_key: str | None,
    overwrite: bool,
    check_only: bool,
    enable_checks: tuple[str, ...],
    disable_checks: tuple[str, ...],
) -> None:
    """Check and fix accessibility issues in documents.

    Reads INPUT_FILE, runs WCAG accessibility checks, and optionally
    fixes issues. By default, all checks are enabled and fixes are applied.
    """
    fix_mode = not check_only

    if fix_mode and not api_key:
        raise click.UsageError(
            "API key required for fix mode. Use --api-key, "
            "set ANTHROPIC_API_KEY, or use --check for report-only mode."
        )

    source = input_file.read_text(encoding="utf-8")
    base_dir = input_file.parent.resolve()

    result_text, check_results = process_document(
        source,
        input_format=input_format,
        output_format=output_format,
        api_key=api_key or "",
        base_dir=base_dir,
        overwrite=overwrite,
        fix=fix_mode,
        enabled_checks=list(enable_checks) if enable_checks else None,
        disabled_checks=list(disable_checks) if disable_checks else None,
    )

    if fix_mode:
        if output_file:
            output_file.write_text(result_text, encoding="utf-8")
            click.echo(f"altscribe: wrote {output_file}", err=True)
        else:
            click.echo(result_text)
    else:
        total = sum(len(r.issues) for r in check_results)
        raise SystemExit(1 if total > 0 else 0)
