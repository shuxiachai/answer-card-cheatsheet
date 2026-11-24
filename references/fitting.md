# Fitting the sheet to two pages

Always measure with `scripts/measure_layout.py` after each build; the numbers below are what one real 2-page sheet gained, so use them to choose the order of moves, not as promises.

## Read the measure output in this order

1. `pages=… spare/OVERFLOW …` — how far you are from the target.
2. `columns end early` — a column whose bottom stayed empty because the next block (card title + Q line + first point, a code block or a figure) is kept together and did not fit, so it moved to the next column. This is the cheapest overflow fix: save 1–2 lines anywhere above the gap in that column and the block moves back, gaining the whole gap. Conversely, cutting lines elsewhere can gain nothing while such a gap absorbs them.
3. The short-last-line list — the next cheapest savings.

## Moves that cost nothing visible (already in the build script)

| Move | Gain on one sheet |
|---|---|
| Widow/orphan control off | ≈ 12 lines (Word otherwise leaves empty lines at column bottoms) |
| Strip leading ★ marks when printing | ≈ 14 lines (some title bars stopped wrapping) |
| No space before title bars / mini cards | ≈ 14 + 5 lines |

## Measured compression ladder (apply top-down, re-measure each time)

| Move | Gain | Cost |
|---|---|---|
| Save 1–2 lines above a column-bottom gap so the pushed block moves back | the whole gap (often 3–4 lines) | none |
| Shorten paragraphs whose last line is < 25 % full (2–4 words each, keep every point) | up to ≈ 30 lines | changes the copy-ready sentences; the user should reread them |
| Column gap 0.2 → 0.1 cm | ≈ 12 lines | text close to the rule |
| Column gap 0.1 → 0.05 cm (build argument 5; measure with `--gap-cm 0.05`) | ≈ 1 line on one sheet | at 0 the rule runs through the first letters |
| Inline code Arial Narrow | ≈ 12–16 lines | code less distinct |
| Line height 1.2 → 1.18 × font | ≈ 10–16 lines | barely visible |
| Font 5 → 4.5 pt (the default since; smaller sizes were not tested) | ≈ 160 lines (1.4 columns) | must pass a print test |

Moves that did **not** pay off: letter spacing −0.1 pt (crowded on paper), Arial Narrow for body text (hard to read), hyphenation (split words get copied wrongly), column gap 0 (the separator rule touches the letters), code at 4.5 pt (≈ 2 lines), Tahoma/Verdana (too wide), Calibri (small x-height).

## Too little content

When the material does not fill two sides (`measure_layout.py` then prints the font size that would roughly fill them), never invent content. In this order:

1. Enlarge the font: rebuild with that size (argument 3 of the build, e.g. 6 or 7 pt), measure again and adjust; larger text is easier to read in the exam, so a print test matters less.
2. Promote: give a likely comparison or calculation from a Summary page its own answer card, and add a worked example from the material to calculation cards.
3. Accept fewer pages or some white space, and say so in the delivery.

## Finding short last lines

`measure_layout.py --short 0.25` lists paragraphs whose last printed line is less than a quarter full. Cutting slightly more characters than that last line holds (fill × ≈ 66 characters at 5 pt, × ≈ 73 at 4.5 pt, plus a few) usually saves the line. Prefer cutting redundant phrases, long synonyms or secondary examples; never cut a marking point, and cut the exam's own keywords last (titles and markers look for them; wording cut only to make a card end at the side boundary was later put back). If a cut does not save the line, a long word at the end of the previous line is probably not moving up: `measure_layout.py --lines "<text of the paragraph>"` prints every line with its fill. Use `--no-points` when the user does not want answer-card points touched.

## Adding without a new line

`measure_layout.py --lines "<text>"` prints how full each line of a paragraph is (a fill, not a position on the page). Words added to a paragraph whose last line still has room cost no line: at 4.5 pt with 0 margins a CJK character or full-width bracket takes ≈ 2.7 % of a line and a Latin character ≈ 1.4 %. Use this for glosses and short additions when the sheet is full, then check the PDF: Word may break a line before a （ or inside Chinese text, which separates a gloss from its word.

## When content still does not fit

Swap, do not squeeze: first remove one-liners that repeat a point already on a card, then one-liners that the review lecture does not name, no quiz asked about and no Summary page mentions, and put the higher-priority gaps in their place. Record each removed block in the gap list with the reason (format.md §1). Merging a gap into an existing card or one-liner usually costs ~1 line, a new one-liner 2–4 lines.

A figure is the most expensive block (≈ 5.3 lines per cm at 4.5 pt): before cutting points, shrink it (`![70%](…)`) or replace it with a text diagram.

## Pitfalls seen in practice

- Word COM: querying `Styles`/`Paragraphs` before export once hung Word for minutes — make edits in python-docx and use COM only to open, export and close (≈ 3–5 s per file).
- Exact line height crops an inline image to a single line; the build script gives figure paragraphs single line height, but images inside tables or next to text are not handled.
- A PDF open in a viewer cannot be overwritten ("Device or resource busy") — ask the user to close it.
- pandoc puts the inline-code character style on code-block runs too; the build script resets those runs to Consolas and keeps the block in one column.
- Long inline code without spaces wraps badly; add spaces inside JSON/XML examples.
- Keep a backup of the master before bulk edits, and after any layout change update documents that cite card positions.
- Uneven letter spacing (letters clustering or touching at 4.5 pt): Word puts each letter on a 0.75 pt (96 dpi) grid when the document is in compatibility mode or when the Windows default printer cannot be reached (e.g. a network print queue). The build sets Word 2013+ layout and `export_pdf.ps1` selects Microsoft Print to PDF for its own Word session. `measure_layout.py` checks every PDF it measures: it counts the letter steps (differences between consecutive `chars` x positions in PyMuPDF's `page.get_texttrace()`) that are whole multiples of 0.75 pt and warns above 50 % (a good export shows ≈ 0.2 %, a snapped one ≈ 99 %). Never set `Word.ActivePrinter` through COM: it changes the Windows default printer.
- The same words can occur in several cards, so `measure_layout.py --find` lists every place a phrase appears. For positions to write into another document use `--cards sheet.md`, which follows the master's order.
- With the user's agreement, cards may run on from side A to side B (only the title, Q line and first point are kept together); then nothing needs shortening just to end side A between cards.
- When the sheet is filled to less than a line of slack, print the PDF: its layout is fixed, while the `.docx` reflows with another Word version or default printer.
