---
name: answer-card-cheatsheet
description: Build a dense, colour-coded, exactly-two-page A4 exam cheatsheet in the "答题卡" (answer-card) format — every likely exam question gets a card of numbered, copy-ready English sentences with Chinese search tags, laid out in 5 newspaper columns by a bundled Markdown→Word script. Use this whenever the user wants to make, rebuild, compress, recolour, re-prioritise or fill an exam cheatsheet / crib sheet / 小抄 / 答题卡 / one-page (A4 double-sided) notes for an open-book or restricted-open-book exam, wants their notes "to look like last time", or asks how to fit more onto the sheet — even if they do not say "skill" or "答题卡".
---

# Answer-card cheatsheet

Produces a cheatsheet the student can *copy from* in the exam: find the question in a card's Q line, copy the numbered English sentences it points to. Output: a Markdown master (`.md`), the printable Word file (`.docx`) and a PDF preview — A4 landscape, 0 margins, 5 columns, exactly two pages (one sheet, double-sided).

The format was refined through repeated printing tests; the details below are what survived them. Follow them unless the user asks otherwise.

## Files in this skill

- `scripts/build_cheatsheet.py` — Markdown master → `.docx` with the full layout (fonts, colours, columns, spacing). `python build_cheatsheet.py sheet.md [out.docx] [font_pt=5] [margin_cm=0]`
- `scripts/export_pdf.ps1` — Word (COM) export of the `.docx` to PDF on Windows.
- `scripts/measure_layout.py` — page count, spare or overflow lines, paragraphs with short last lines, and where given text sits (side / column / height).
- `references/format.md` — the exact Markdown syntax of every block, writing rules per question type, layout spec and colour palette. **Read it before writing any content.**
- `references/fitting.md` — how to land on exactly two pages: measured compression ladder, trimming, filling, and pitfalls.
- `assets/example.md` — a short real master to copy the look from.

## Workflow

### 1. Collect what the exam rewards

Ask for (or find in the project) the exam rules (sheet size and sides, language, date), the **review / revision lecture** (examinable topics and example questions), **sample exam(s)** with official answers if any, quizzes, lecture slides (especially their *Summary* / *Review* pages) and tutorials. The review lecture and the sample exam are the strongest priority signals; Summary pages come next; quiz questions show the MCQ style.

When there are many lecture PDFs, extract the text with PyMuPDF and split the reading across parallel subagents (2–3 lectures each), asking each to report, per page, the concepts not yet on the sheet with an importance rating and the reason. Verify a sample of what they report against the master before acting on it.

### 2. Decide tiers

- **★★★★ answer card** — every sample-exam question, every example question in the review lecture, plus answer-method cards (a scenario/design-question framework whose points start with the official sub-headings; a tool menu; a format-description template). 4–7 sentences, each ≈ 1 mark.
- **★★★ mini card** — every topic the review lecture names that has no card yet; 1–2 sentences.
- **★★ one-liner** — Summary-page points, quiz facts, typical MCQ traps, and **code templates** for variant code questions (SQL with WHERE/GROUP BY/HAVING, DDL with keys, the course's library calls). One sentence, sometimes with inline code.

Keep a gap list (what is not on the sheet, with lecture/page and importance) — it is what you fill from when space frees up and what you swap against when it does not.

### 3. Write the master

Follow `references/format.md` exactly: header notes (not printed), the line `## 答题卡`, then blocks **grouped by topic** in lecture order — first the answer-method group, then for each topic its answer cards → mini cards → one-liners. Every mini card and one-liner starts with a colour key such as `{W9}`; answer cards take their colour from the 〔topic〕 in the title. Sentences are complete English sentences (the review lecture asks for them), self-contained (no "It/This" pointing back), with code in backticks.

Paraphrase lecture and exam material in your own words; never paste slide text or exam questions verbatim.

### 4. Build, export, measure

```bash
python scripts/build_cheatsheet.py sheet.md sheet.docx 5        # or 4.5 if the print test is fine
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/export_pdf.ps1 -Docx <abs path>.docx -Pdf <abs path>.pdf
python scripts/measure_layout.py sheet.pdf --font 5 --short 0.25 --find "TCP vs UDP" "Subnetting"
```

The build needs `pandoc` (≥ 2.x) and `python-docx`. If `pandoc` is not on PATH, look for a bundled copy (RStudio/Quarto ship one under `…/quarto/bin/tools/`) and prepend its folder to PATH for the build only.

### 5. Fit to exactly two pages

Use `references/fitting.md`. In short: overflow → first shorten paragraphs whose last printed line is nearly empty (a few words each, no points lost), then drop the lowest-priority one-liners; spare space → add from the gap list in priority order. Leave 1–2 lines of slack so a different Word/printer does not spill onto page 3. Never go past two pages.

### 6. Verify and deliver

- Every sample-exam part and review-lecture example question can be answered by copying sentences from one card; check the Q lines point to the right numbers.
- Re-measure after every change, and if other documents quote card locations (e.g. a sample-exam answer key "B side, column 2, middle"), update them.
- Ask the user to **print one copy** and check legibility before the exam; small fonts read differently on paper than on screen.
- Deliver `.md` (master — edit this, not the `.docx`), `.docx` (print this) and `.pdf` (preview). Keep the previous version when making a variant (e.g. a 4.5 pt edition) instead of overwriting it.

## Defaults that came from printing tests

- Body font Segoe UI (Latin) + 微软雅黑 (CJK) at normal letter spacing — condensed Arial looked crowded on paper; Segoe UI is about as compact and clearer.
- 5 pt, exact line height = 1.18 × font size (5 pt → 5.9 pt); 4.5 pt was still readable in a print test and frees ≈ 1.4 columns.
- Inline code Arial Narrow (saves ≈ 12 lines); code blocks Consolas and kept in one column (a DOM tree needs monospace alignment).
- One size for everything; titles stand out by fill, colour and bold only. The per-element font / weight / colour / background table is in `references/format.md` → "Font and style table", including what to change when a font is missing.
- 0 margins printed fine on an ordinary office laser printer; use 0.5 cm if a printer clips the edges.
- No answer-template card: generic sentence frames proved low value once every card is written in those patterns.
