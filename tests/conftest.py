"""Shared test fixtures + environment gates.

Most altscribe tests route through panflute → pandoc for Markdown parsing.
If the pandoc binary is not installed on the runner we skip those tests
cleanly rather than fail — this keeps the PyPI install verifiable even
on hosts without pandoc.
"""
import pathlib
from shutil import which

import pytest


def pytest_collection_modifyitems(config, items):
    if which("pandoc") is not None:
        return
    skip_pandoc = pytest.mark.skip(reason="pandoc binary not installed")
    for item in items:
        # Only skip tests that actually invoke process_document / panflute.
        src = item.module.__file__
        try:
            text = pathlib.Path(src).read_text(encoding="utf-8")
        except Exception:
            continue
        if "process_document" in text or "panflute" in text:
            item.add_marker(skip_pandoc)
