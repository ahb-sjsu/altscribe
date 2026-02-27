# I Built an Open-Source Tool to Solve One of Higher Ed's Biggest Accessibility Gaps

The ADA Title II deadline is less than two months away. By April 24, 2026, every public university in the country must meet WCAG 2.1 Level AA — and the single most common accessibility failure in digital course materials is still the same one it's been for years: missing image alt text.

Faculty produce thousands of documents every semester — lecture slides, syllabi, lab manuals, research posters — and every embedded image without alt text is a barrier for students using screen readers. The fix is conceptually simple (describe the image), but the volume makes it impractical to do manually at scale.

So I built **altscribe** — an open-source CLI tool that reads any document format, uses AI vision to classify and describe every image, and outputs an accessible version with compliant alt text injected automatically.

## What makes it different

Most alt-text generators produce a one-size-fits-all description. altscribe classifies each image into one of five W3C WAI categories and applies the correct strategy for each:

- **Decorative images** (borders, spacers, flourishes) get `alt=""` so screen readers skip them entirely — instead of narrating "blue horizontal line" to a student trying to read a syllabus
- **Informative images** (photos, illustrations) get concise descriptions focused on what the image communicates in context, not exhaustive visual detail
- **Functional images** (logos or icons used as links/buttons) describe the *action* — "Navigate to homepage," not "university seal with laurel wreath"
- **Complex images** (charts, graphs, diagrams) get both a short alt label *and* a structured long description with all the data, trends, and takeaways — because a bar chart can't be meaningfully described in 125 characters
- **Images of text** (scanned handouts, screenshots) get a verbatim transcription, satisfying WCAG SC 1.4.5

This is the level of nuance that actual accessibility auditors look for, and it's what the W3C WAI Images Tutorial specifies.

## How it works

altscribe is a pandoc wrapper. It parses your document into an AST, walks every image node, sends each one to Claude's vision API with surrounding document context (section headings, adjacent text), and injects the generated alt text back into the document tree. It reads and writes anything pandoc supports — Markdown, HTML, DOCX, LaTeX, RST, and more.

```
pip install altscribe
altscribe lecture-notes.md -o lecture-notes-accessible.md
```

That's it. One command, and every image in the file gets tagged.

## Why this matters for CSU — and every public university

The California State University system serves nearly 460,000 students across 23 campuses. Under the CSU Accessible Technology Initiative, Executive Order 1111, and the 2024 ADA Title II Final Rule, all digital instructional content must conform to WCAG 2.1 Level AA by April 24, 2026.

The regulations that apply:
- ADA Title II (2024 Final Rule) — WCAG 2.1 AA by April 2026
- Section 508 (Revised 2017) — WCAG 2.0 AA, ongoing
- California Government Code 11135 — Section 508 compliance for state entities
- California AB 434 — Biennial WCAG certification for state agency websites

Faculty are the ones producing the content, but most don't have the time or training to write effective alt text for every image in every document. altscribe is designed to close that gap — draft compliant alt text at the speed of a CLI command, so faculty can review and publish rather than starting from scratch.

## Important caveat

AI-generated alt text should always be reviewed by a human. altscribe is a productivity tool that produces a compliant first draft — final responsibility for accessibility rests with the content author. But going from a blank alt attribute to a solid starting description cuts the work from minutes per image down to seconds.

## Try it

- **Install:** `pip install altscribe`
- **GitHub:** https://github.com/ahb-sjsu/altscribe
- **PyPI:** https://pypi.org/project/altscribe/

The project is MIT licensed. Contributions, issues, and feedback are welcome.

If you work in higher ed accessibility, digital content strategy, or instructional design — I'd love to hear how you're approaching the Title II deadline and whether a tool like this would fit into your workflow.

#Accessibility #HigherEducation #WCAG #ADA #OpenSource #Python #CSU #a11y #EdTech
