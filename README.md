# altscribe

[![CI](https://github.com/ahb-sjsu/altscribe/actions/workflows/ci.yaml/badge.svg)](https://github.com/ahb-sjsu/altscribe/actions/workflows/ci.yaml)
[![PyPI](https://img.shields.io/pypi/v/altscribe)](https://pypi.org/project/altscribe/)
[![Python 3.10+](https://img.shields.io/pypi/pyversions/altscribe)](https://pypi.org/project/altscribe/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI-powered, WCAG 2.1 AA compliant image alt-text generator for documents — built on [pandoc](https://pandoc.org/) and [Claude](https://www.anthropic.com/claude).

Designed for **California State University faculty** to meet accessibility obligations under ADA Title II, Section 508, and the [CSU Accessible Technology Initiative](https://ati.calstate.edu/).

## Features

- **Automatic image classification** — detects decorative, informative, functional, complex, and text images per the [W3C WAI Images Tutorial](https://www.w3.org/WAI/tutorials/images/)
- **WCAG 2.1 Level AA compliant** (SC 1.1.1 Non-text Content, SC 1.4.5 Images of Text)
- **Context-aware** — passes surrounding text and section headings to the model for better descriptions
- **Complex image support** — generates both short alt-text and structured long descriptions for charts, graphs, and diagrams
- **Functional image detection** — identifies images inside links/buttons and describes the action, not appearance
- **Decorative image handling** — produces empty `alt=""` for non-informational images
- **Images of text** — transcribes visible text verbatim
- **Any format in, any format out** — leverages pandoc to read and write Markdown, HTML, DOCX, RST, LaTeX, and more

## Installation

### Prerequisites

- Python 3.10+
- [pandoc](https://pandoc.org/installing.html) installed and on PATH
- An [Anthropic API key](https://console.anthropic.com/)

### Install from PyPI

```bash
pip install altscribe
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

# Process a Markdown file
altscribe lecture-notes.md -o lecture-notes-accessible.md

# Convert HTML to accessible Markdown
altscribe syllabus.html -f html -t markdown -o syllabus.md

# Regenerate alt-text even for images that already have it
altscribe slides.md --overwrite -o slides-fixed.md

# Output to stdout
altscribe document.md
```

### Options

| Flag | Description |
|---|---|
| `-o, --output FILE` | Output file path (default: stdout) |
| `-f, --from FORMAT` | Pandoc input format (default: auto-detect) |
| `-t, --to FORMAT` | Pandoc output format (default: markdown) |
| `--api-key KEY` | Anthropic API key (or set `ANTHROPIC_API_KEY`) |
| `--overwrite` | Regenerate alt-text for images that already have it |

## How It Works

1. **Parse** — reads the input document into a pandoc AST via [panflute](https://github.com/sergiocorreia/panflute)
2. **Walk** — traverses every `Image` node in the document
3. **Classify** — sends each image to Claude's vision API, which classifies it into one of five W3C WAI categories (decorative, informative, functional, complex, text)
4. **Generate** — produces category-appropriate alt-text:
   - *Decorative*: `alt=""`
   - *Informative*: concise description under 125 characters
   - *Functional*: describes the action/destination of the parent link or button
   - *Complex*: short alt-text plus a structured long description inserted after the image
   - *Text*: verbatim transcription of all visible text
5. **Output** — writes the modified document in any pandoc-supported format

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
- **1.4.5 Images of Text (Level AA)** — text in images is transcribed verbatim

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
