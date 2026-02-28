# altscribe

[![CI](https://github.com/ahb-sjsu/altscribe/actions/workflows/ci.yaml/badge.svg)](https://github.com/ahb-sjsu/altscribe/actions/workflows/ci.yaml)
[![PyPI](https://img.shields.io/pypi/v/altscribe)](https://pypi.org/project/altscribe/)
[![Python 3.10+](https://img.shields.io/pypi/pyversions/altscribe)](https://pypi.org/project/altscribe/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI-powered WCAG 2.1 AA document accessibility checker and fixer — built on [pandoc](https://pandoc.org/) and [Claude](https://www.anthropic.com/claude).

Designed for **California State University faculty** to meet accessibility obligations under ADA Title II, Section 508, and the [CSU Accessible Technology Initiative](https://ati.calstate.edu/).

## Features

### Accessibility Checks

| Check | WCAG SC | Detects | Auto-fix |
|---|---|---|---|
| **Image Alt-Text** | 1.1.1, 1.4.5 | Missing/inadequate alt-text on images | AI-generated alt-text by image type |
| **Heading Hierarchy** | 1.3.1, 2.4.6 | Missing H1, skipped levels, empty headings, fake headings (bold paragraphs) | Re-levels headings, promotes fake headings |
| **Link Text Quality** | 2.4.4 | "Click here", bare URLs, empty links, duplicate text with different URLs | AI-suggested descriptive replacements |
| **Table Accessibility** | 1.3.1 | Missing captions, empty table headers | AI-generated captions |
| **Document Language** | 3.1.1 | Missing `lang` attribute | Auto-detects language via `langdetect` |
| **List Structure** | 1.3.1 | Fake lists (bullet/numbered paragraphs not using list markup) | Converts to proper list elements |

### Core Capabilities

- **Automatic image classification** — detects decorative, informative, functional, complex, and text images per the [W3C WAI Images Tutorial](https://www.w3.org/WAI/tutorials/images/)
- **Check-only mode** — report issues without making changes or API calls (`--check`)
- **Selective checks** — enable/disable individual checks (`--enable`, `--disable`)
- **Context-aware AI** — passes surrounding text and section headings to Claude for better descriptions
- **Complex image support** — generates both short alt-text and structured long descriptions for charts, graphs, and diagrams
- **Any format in, any format out** — leverages pandoc to read and write Markdown, HTML, DOCX, RST, LaTeX, and more

## Installation

### Prerequisites

- Python 3.10+
- [pandoc](https://pandoc.org/installing.html) installed and on PATH
- An [Anthropic API key](https://console.anthropic.com/)

### Install from PyPI

```bash
pip install altscribe

# With automatic language detection (for document-language check)
pip install altscribe[language]
```

### Install from source

```bash
git clone https://github.com/ahb-sjsu/altscribe.git
cd altscribe
pip install -e .
```

## Usage

```bash
# Set your API key (or pass --api-key)
export ANTHROPIC_API_KEY=sk-ant-...

# Fix all accessibility issues in a Markdown file
altscribe lecture-notes.md -o lecture-notes-accessible.md

# Check only — report issues without fixing (no API calls, free)
altscribe --check lecture-notes.md

# Run only specific checks
altscribe --enable heading-hierarchy --enable link-text --check doc.md

# Skip certain checks
altscribe --disable image-alt-text doc.md -o fixed.md

# Convert HTML to accessible Markdown
altscribe syllabus.html -f html -t markdown -o syllabus.md

# Regenerate alt-text even for images that already have it
altscribe slides.md --overwrite -o slides-fixed.md
```

### Options

| Flag | Description |
|---|---|
| `-o, --output FILE` | Output file path (default: stdout) |
| `-f, --from FORMAT` | Pandoc input format (default: auto-detect) |
| `-t, --to FORMAT` | Pandoc output format (default: markdown) |
| `--api-key KEY` | Anthropic API key (or set `ANTHROPIC_API_KEY`). Only required in fix mode. |
| `--overwrite` | Regenerate alt-text for images that already have it |
| `--check` | Report-only mode — no fixes, no API calls. Exit code 1 if issues found. |
| `--enable ID` | Only run specific check(s). Repeatable. |
| `--disable ID` | Skip specific check(s). Repeatable. |

### Available Check IDs

`image-alt-text`, `heading-hierarchy`, `link-text`, `table-accessibility`, `document-language`, `list-structure`

## How It Works

1. **Parse** — reads the input document into a pandoc AST via [panflute](https://github.com/sergiocorreia/panflute)
2. **Walk** — traverses the AST once, dispatching each element to registered checkers (headings, images, links, tables, lists, etc.)
3. **Analyze** — each checker accumulates issues: missing alt-text, skipped heading levels, generic link text, fake lists, and more
4. **Fix** (unless `--check`) — checkers apply auto-fixes: AI-generated alt-text, re-leveled headings, proper list markup, language tags
5. **Report** — prints a summary of all issues found and fixed to stderr
6. **Output** — writes the modified document in any pandoc-supported format

## Compliance

altscribe is designed to satisfy the following standards as they apply to CSU:

| Regulation | Standard | Deadline |
|---|---|---|
| ADA Title II (2024 Final Rule) | WCAG 2.1 Level AA | April 24, 2026 |
| Section 508 (Revised 2017) | WCAG 2.0 Level AA | Ongoing |
| California Gov. Code 11135 | Section 508 compliance | Ongoing |
| California AB 434 | WCAG 2.0 Level AA+ | Biennial |
| CSU Executive Order 1111 | CSU ATI Policy | Ongoing |

### WCAG success criteria addressed

- **1.1.1 Non-text Content (Level A)** — all images receive appropriate text alternatives
- **1.3.1 Info and Relationships (Level A)** — headings, tables, and lists use proper semantic markup
- **1.4.5 Images of Text (Level AA)** — text in images is transcribed verbatim
- **2.4.4 Link Purpose (Level A)** — link text is descriptive and non-generic
- **2.4.6 Headings and Labels (Level AA)** — heading hierarchy is logical and complete
- **3.1.1 Language of Page (Level A)** — document language attribute is present

### Image handling per W3C WAI guidelines

| Image type | alt-text strategy | Long description |
|---|---|---|
| Decorative | `alt=""` | No |
| Informative | Concise description | No |
| Functional | Action/destination label | No |
| Complex (charts, diagrams) | Short identifying label | Yes — inserted as adjacent text block |
| Images of text | Verbatim transcription | No |

> **Note:** AI-generated alt-text should be reviewed by a human for accuracy. altscribe is a productivity tool that drafts compliant alt-text — final responsibility for accessibility rests with the content author.

## Development

```bash
# Install dev dependencies
pip install -e . ruff black pytest

# Run tests
pytest tests/ -v

# Lint
ruff check src/ tests/

# Format
black src/ tests/
```

## License

[MIT](LICENSE)
