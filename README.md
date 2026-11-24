# answer-card-cheatsheet

A Claude Code skill that builds a dense, colour-coded, exactly-two-page A4 exam cheatsheet in the "答题卡" (answer-card) format: every likely exam question gets a card of numbered, copy-ready English sentences with Chinese search tags, laid out in 5 newspaper columns from a Markdown master.

一个 Claude Code skill：按「答题卡」格式做考试 cheatsheet（A4 横向、正好两页、5 栏、按主题配色）。每张卡对应一道可能的考题，配可以直接抄进试卷的英文句子和方便查找的中文标签。

## Install

Copy this folder to your personal skills directory, then start a new Claude Code session:

```bash
git clone https://github.com/shuxiachai/answer-card-cheatsheet.git ~/.claude/skills/answer-card-cheatsheet
```

On Windows the directory is `C:\Users\<you>\.claude\skills\answer-card-cheatsheet`.

Then ask Claude Code something like "帮我做一份这门课的 cheatsheet" or "make an exam cheatsheet in the answer-card format".

## Requirements

- Python 3 with `python-docx` and `PyMuPDF` (`pip install python-docx pymupdf`)
- `pandoc` 2.x or newer: on PATH, named by the `PANDOC` environment variable, or the copy bundled with RStudio / Quarto (found automatically)
- Microsoft Word on Windows for `scripts/export_pdf.ps1` (or export the `.docx` to PDF any other way)

## Contents

| Path | What it is |
|---|---|
| `SKILL.md` | Workflow: collect exam signals, tier the content, write the master, build, fit to two pages, verify |
| `references/format.md` | Exact Markdown syntax of every block, writing rules per question type, colour palette, layout spec |
| `references/fitting.md` | How to land on two pages: column-bottom gaps, measured compression ladder, too little content, trimming, pitfalls |
| `scripts/check_master.py` | Checks the master before building (colours, Q-line references, numbering, tags, lengths, figures) |
| `scripts/build_cheatsheet.py` | Markdown master → `.docx` (`python build_cheatsheet.py sheet.md [out.docx] [font_pt=4.5] [margin_cm=0] [gap_cm=0.1]`); figures via `![60%](fig.png)` |
| `scripts/export_pdf.ps1` | Word export of the `.docx` to PDF (relative or absolute paths); uses Microsoft Print to PDF for its own Word session so small text is evenly spaced |
| `scripts/measure_layout.py` | Page count, spare lines, short last lines, where given text sits (font size and margin detected from the PDF) |
| `assets/example.md` | A short made-up master (Computer Networks) showing the format |
