---
name: answer-card-cheatsheet
description: Build a dense, colour-coded, exactly-two-page A4 exam cheatsheet in the "答题卡" (answer-card) format — every likely exam question gets a card of numbered, copy-ready English sentences with Chinese search tags, laid out in 5 newspaper columns by a bundled Markdown→Word script. Use this whenever the user wants to make, rebuild, compress, recolour, re-prioritise or fill an exam cheatsheet / crib sheet / 小抄 / 答题卡 / one-page (A4 double-sided) notes for an open-book or restricted-open-book exam, wants their notes "to look like last time", or asks how to fit more onto the sheet — even if they do not say "skill" or "答题卡".
---

# Answer-card cheatsheet

Produces a cheatsheet the student can *copy from* in the exam: find the question in a card's Q line, copy the numbered English sentences it points to. Output: a Markdown master (`.md`), the printable Word file (`.docx`) and a PDF preview — A4 landscape, 0 margins, 5 columns, exactly two pages (one sheet, double-sided).

The format was refined through repeated printing tests; the details below are what survived them. Follow them unless the user asks otherwise.

## Files in this skill

Paths are relative to this skill's directory (the base directory shown when the skill loads, written `<skill>` below); the user's files stay in their own project folder.

- `scripts/check_master.py` — checks the Markdown master before building: errors the build would get wrong (uncoloured or shifted colours, unknown colour keys, Q lines pointing to missing points, broken numbering, unpaired `**`) and reminders from the format rules (missing Q line, unrecognised tag, Chinese in an English sentence, too long), plus each figure's height in lines and minimum label size at the size given with `--font` (default 5). Exit code 1 on errors.
- `scripts/build_cheatsheet.py` — Markdown master → `.docx` with the full layout (fonts, colours, columns, spacing). `python build_cheatsheet.py sheet.md [out.docx] [font_pt=5] [margin_cm=0]`; it also prints warnings such as a card title without `**`. Figures (`![60%](fig.png)` on their own line) are scaled to the column.
- `scripts/export_pdf.ps1` — Word (COM) export of the `.docx` to PDF on Windows; relative paths are fine.
- `scripts/measure_layout.py` — page count, spare or overflow lines (figures included), columns that end early because the next kept-together block was pushed on, paragraphs with short last lines (`pt` = answer-card point; `--no-points` hides them), where given text sits (`--find`), and every line of a paragraph with its fill (`--lines`). When the content fills far less than two sides it suggests a font size. Font size and margin are read from the PDF.
- `references/format.md` — the exact Markdown syntax of every block, writing rules per question type, layout spec and colour palette. **Read it before writing any content.**
- `references/fitting.md` — how to land on two pages: reading the measure output, column-bottom gaps, the measured compression ladder, too little content, trimming, and pitfalls.
- `assets/example.md` — a short made-up master (Computer Networks) to copy the look from.

## Workflow

### 1. Collect what the exam rewards

Ask for (or find in the project) the exam rules (sheet size and sides, language, date), the **review / revision lecture** (examinable topics and example questions), **sample exam(s)** with official answers if any, quizzes, lecture slides (especially their *Summary* / *Review* pages) and tutorials. The review lecture and the sample exam are the strongest priority signals; Summary pages come next; quiz questions show the MCQ style.

When there are many lecture PDFs, extract the text with PyMuPDF and split the reading across parallel subagents (2–3 lectures each), asking each to report, per page, the concepts not yet on the sheet with an importance rating and the reason. Verify a sample of what they report against the master before acting on it.

### 2. Decide tiers

- **★★★★ answer card** — every sample-exam question and every example question in the review lecture. A comparison or calculation that a Summary page names also gets one when space allows. 4–7 sentences, each ≈ 1 mark.
- **Answer-method group** (first on the sheet) — only for question types this exam actually has: a scenario/design-question framework whose points start with the official sub-headings, a tool menu, a format-description template. If the exam has none of these, keep a single `{EXAM}` mini card with the review lecture's answering advice, or leave the group out.
- **★★★ mini card** — every topic the review lecture names that has no card yet; 1–2 sentences.
- **★★ one-liner** — Summary-page points, quiz facts, typical MCQ traps, and **code templates** for variant code questions (SQL with WHERE/GROUP BY/HAVING, DDL with keys, the course's library calls). One sentence, sometimes with inline code.

Keep a gap list (what is not on the sheet, with lecture/page and importance) in the master's header notes, which are not printed. It is what you fill from when space frees up and what you swap against when it does not.

### 3. Write the master

Follow `references/format.md` exactly: header notes (not printed), the line `## 答题卡`, then blocks **grouped by topic** in lecture order — first the answer-method group, then for each topic its answer cards → mini cards → one-liners. Answer cards take their colour from the 〔topic〕 in the title; every mini card and one-liner starts with the colour key of its topic's answer cards, such as `{W9}` (format.md §4 — with the default mapping, topic 1 is `{W2}`). Sentences are complete English sentences (the review lecture asks for them), self-contained (no "It/This" pointing back), with code in backticks.

Draw diagrams as text (a code block with ├─ └─, a line of arrows, a table); add an image only when the shape itself is the answer, and weigh its cost in lines (`references/format.md` → Figures).

Paraphrase lecture and exam material in your own words; never paste slide text or exam questions verbatim.

### 4. Check, build, export, measure

Run these from the folder that holds the master:

```bash
python <skill>/scripts/check_master.py sheet.md --font 5              # fix every error; read the reminders
python <skill>/scripts/build_cheatsheet.py sheet.md sheet.docx 5      # or 4.5 if the print test is fine
powershell -NoProfile -ExecutionPolicy Bypass -File <skill>/scripts/export_pdf.ps1 -Docx sheet.docx -Pdf sheet.pdf
python <skill>/scripts/measure_layout.py sheet.pdf --short 0.25 --find "TCP vs UDP" "Subnetting"
```

`measure_layout.py` prints the font size and margin it detected on its first line; pass `--font` / `--margin-cm` only if those look wrong.

The build needs `pandoc` (≥ 2.x) and `python-docx`. It finds pandoc by itself on PATH, through the `PANDOC` environment variable, or in the copy bundled with RStudio (`<RStudio>/resources/app/bin/quarto/bin/tools/pandoc.exe`) or Quarto (`<Quarto>/bin/tools/`). If it still reports pandoc missing, install pandoc, or point `PANDOC` at the executable for the build only — PowerShell: `$env:PANDOC = 'D:\path\to\pandoc.exe'; python …`, bash: `PANDOC=/path/to/pandoc python …`.

### 5. Fit to two pages

Use `references/fitting.md`. In short, read the measure output top-down:
- **Overflow:** first pull back blocks pushed to the next column (the "columns end early" list: save 1–2 lines above that gap), then shorten paragraphs whose last printed line is nearly empty (a few words each, no points lost), then drop the lowest-priority one-liners.
- **Spare space:** add from the gap list in priority order.
- **Far too little content** (the script then suggests a font size): see "Too little content" in fitting.md. Never invent content to fill space.

Leave 1–2 lines of slack so a different Word or printer does not spill onto page 3. Never go past two pages.

### 6. Verify and deliver

- `check_master.py` reports no errors.
- Every sample-exam part and review-lecture example question can be answered by copying sentences from one card; check that the Q lines point to the right numbers (the script only checks that those numbers exist).
- Re-measure after every change, and if other documents quote card locations (e.g. a sample-exam answer key "B side, column 2, middle"), update them.
- Ask the user to **print one copy** and check legibility before the exam; small fonts read differently on paper than on screen.
- The PDF has at most two pages: exactly two when the material fills them, otherwise what it fills at the chosen size.
- Deliver `.md` (master — edit this, not the `.docx`), `.docx` (print this) and `.pdf` (preview). Keep the previous version when making a variant (e.g. a 4.5 pt edition) instead of overwriting it.

## Editing an existing sheet

For "add X / replace Y / make it fit again" requests on a sheet that already exists:

1. Back up the master (or save the change under a new version name), then build, export and measure the current version first, and note its spare lines.
2. Make the change in the `.md`, never in the `.docx`. Place new blocks in their topic group (answer cards → mini cards → one-liners); a figure goes directly after the card or mini card it illustrates.
3. Run check, build, export and measure.
4. If it overflows, follow fitting.md: column-bottom gaps first, then short last lines (`--no-points` hides answer-card points when the user protects them), then swap out low-priority one-liners. Never remove an answer-card point without the user's agreement.
5. Report what was added and every sentence that was shortened or removed, and the spare lines before and after.

An explicit user request (e.g. "add this picture") overrides the soft rules here, such as drawing diagrams as text first; mention the cost in lines.

## Defaults that came from printing tests

- Body font Segoe UI (Latin) + 微软雅黑 (CJK) at normal letter spacing — condensed Arial looked crowded on paper; Segoe UI is about as compact and clearer.
- 5 pt, exact line height = 1.18 × font size (5 pt → 5.9 pt); 4.5 pt was still readable in a print test and frees ≈ 1.4 columns.
- Inline code Arial Narrow (saves ≈ 12 lines); code blocks Consolas and kept in one column (a DOM tree needs monospace alignment).
- One size for everything; titles stand out by fill, colour and bold only. The per-element font / weight / colour / background table is in `references/format.md` → "Font and style table", including what to change when a font is missing.
- 0 margins printed fine on an ordinary office laser printer; use 0.5 cm if a printer clips the edges.
- No answer-template card: generic sentence frames proved low value once every card is written in those patterns.
