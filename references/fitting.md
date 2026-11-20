# Fitting the sheet to exactly two pages

Always measure with `scripts/measure_layout.py` after each build; the numbers below are what one real 2-page sheet gained, so use them to choose the order of moves, not as promises.

## Moves that cost nothing visible (already in the build script)

| Move | Gain on one sheet |
|---|---|
| Widow/orphan control off | ≈ 12 lines (Word otherwise leaves empty lines at column bottoms) |
| Strip leading ★ marks when printing | ≈ 14 lines (some title bars stopped wrapping) |
| No space before title bars / mini cards | ≈ 14 + 5 lines |

## Measured compression ladder (apply top-down, re-measure each time)

| Move | Gain | Cost |
|---|---|---|
| Shorten paragraphs whose last line is < 25 % full (2–4 words each, keep every point) | up to ≈ 30 lines | changes the copy-ready sentences; the user should reread them |
| Column gap 0.2 → 0.1 cm | ≈ 12 lines | text close to the rule |
| Inline code Arial Narrow | ≈ 12–16 lines | code less distinct |
| Line height 1.2 → 1.18 × font | ≈ 10–16 lines | barely visible |
| Font 5 → 4.5 pt | ≈ 160 lines (1.4 columns) | must pass a print test |

Moves that did **not** pay off: letter spacing −0.1 pt (crowded on paper), Arial Narrow for body text (hard to read), hyphenation (split words get copied wrongly), column gap 0.05 cm (no gain), code at 4.5 pt (≈ 2 lines), Tahoma/Verdana (too wide), Calibri (small x-height).

## Finding short last lines

`measure_layout.py --short 0.25` lists paragraphs whose last printed line is less than a quarter full. Cutting slightly more characters than that last line holds (fill × ≈ 66 characters at 5 pt, × ≈ 73 at 4.5 pt, plus a few) usually saves the line. Prefer cutting redundant phrases, long synonyms or secondary examples; never cut a marking point.

## When content still does not fit

Swap, do not squeeze: remove one-liners that the review lecture does not name, no quiz asked about and no Summary page mentions, and put the higher-priority gaps in their place. Merging a gap into an existing card or one-liner usually costs ~1 line, a new one-liner 2–4 lines.

A figure is the most expensive block (≈ 4.8 lines per cm at 5 pt): before cutting points, shrink it (`![70%](…)`) or replace it with a text diagram.

## Pitfalls seen in practice

- Word COM: querying `Styles`/`Paragraphs` before export once hung Word for minutes — make edits in python-docx and use COM only to open, export and close (≈ 3–5 s per file).
- Exact line height crops an inline image to a single line; the build script gives figure paragraphs single line height, but images inside tables or next to text are not handled.
- A PDF open in a viewer cannot be overwritten ("Device or resource busy") — ask the user to close it.
- pandoc puts the inline-code character style on code-block runs too; the build script resets those runs to Consolas and keeps the block in one column.
- Long inline code without spaces wraps badly; add spaces inside JSON/XML examples.
- Keep a backup of the master before bulk edits, and after any layout change update documents that cite card positions.
