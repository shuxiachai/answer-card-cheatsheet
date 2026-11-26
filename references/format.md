# Format reference

## Contents
1. File layout
2. Block syntax (answer card, mini card, one-liner, tables, code, figures)
3. Writing rules per question type
4. Colour keys and palette
5. Printed layout (what the build script does)
6. Capacity and self-check

## 1. File layout

```
# <Course> Cheatsheet 答题卡（…）

> Notes for the student and for future edits — NOT printed (everything before "## 答题卡" is skipped).
> 考试: date, sheet rules, sections and marks
> 来源优先级: sample exam + answer guide → review lecture → question bank → Summary pages
> 配色: 1=W1 2=W2 3=W3 A=DESIGN   ← recommended: topic n gets {Wn} (see §4)
> 重建 (run in this folder; the skill's absolute path, every non-default argument):
>   python <skill>/scripts/check_master.py sheet.md --gap-cm 0.05
>   python <skill>/scripts/build_cheatsheet.py sheet.md sheet.docx 4.5 0 0.05
>   powershell -NoProfile -ExecutionPolicy Bypass -File <skill>/scripts/export_pdf.ps1 -Docx sheet.docx -Pdf sheet.pdf
>   python <skill>/scripts/measure_layout.py sheet.pdf --gap-cm 0.05
> 版面: size and why, spare lines, the user's decisions (e.g. cards may run on from side A to B, no white space)
> Gap list (not on the sheet, by importance, with lecture/page):
> - …
> - deleted: <block> — MCQ-only / repeats <card> ③ / to fit

## 怎么用
1. Find the card from the question's English keywords in the titles; the Q line says which points to copy.
2. Copy whole sentences, change only the words in [ ], skip the Chinese in （）.
3. For compare / prioritise / evaluate asks, add one short sentence of your own that states the comparison or the order.

## 答题卡

<blocks, separated by one blank line>
```

The rebuild lines matter most when an argument differs from the default: a sheet built with a 0.05 cm gap must also be measured with `--gap-cm 0.05`. Record deleted blocks with the reason, so they can be restored when space frees up. Keep 怎么用 in step with the sheet: when a card it mentions is deleted, update it.

Order of blocks: a framework card only if the marking guide has fixed sub-headings (SKILL.md step 2), then topic 1, topic 2, … in lecture order; inside each topic: answer cards → mini cards → one-liners.

## 2. Block syntax (symbols must match exactly)

### Answer card (★★★★)

```
**★★★★ 〔1 传输层〕 TCP 与 UDP TCP vs UDP**
Q: Differences between TCP and UDP? → ①–⑤ · When would you use which? → ⑥
① 面向连接 TCP is a connection-oriented transport protocol that delivers a reliable, ordered byte stream between two applications.
② 无连接 UDP is a connectionless transport protocol that sends independent datagrams without guaranteeing delivery or order.
```

- Title line: starts with `**★★★★ `, whole line inside `**` (printed white on the topic-colour bar in regular weight; `--bold-titles` makes it bold); topic tag in 〔number name〕 (`〔A 答题〕` for a framework card) — the build script colours the card from this number; then Chinese name, then English title — or, easier to find from a question, the English keywords a question would use, separated by ` · ` (`**★★★★ 〔1 传输层〕 TCP 与 UDP TCP vs UDP · reliability · handshake · latency · when to use**`). A title may wrap to two lines; the build keeps it in one column. A colour key such as `{DESIGN}` may precede the line to override.
- Q line: `Q: ` + one short cue per sub-question the card answers (usually 2–5, in the sample exam's or question bank's words, paraphrased), each followed by `→` and the point numbers to copy (`①–⑤`, `⑥⑦`); cues separated by ` · `; ≤ 25 English words. Example: `Q: Name the attack → ① · Why encryption does not stop it → ② · Freshness design → ③–⑤`. Chinese notes may follow in （）. A card that is a tool rather than a question (e.g. a template) may use a `用法：…` line instead; it is printed the same way.
- Points: `①`…`⑦`, a space, a tag, a space, one complete English sentence of 15–30 words (≈ 1 mark). Official marking points first, example last or second-to-last. Keep an official answer guide's own wording even when it makes a sentence longer (up to ≈ 40 words) or a card longer (up to ⑧).
- Tag: normally a 2–4 character Chinese tag (定义 / 区别 / 原因 / 选择 / 例子 / 局限 …). In a scenario/design framework card the tag is the official English sub-heading with a colon instead (`① Data Sources:`, up to three words). A tag that contains Latin letters (`TCP定义`, `FCFS`, `TLB`) is not recognised and stays uncoloured, so use a Chinese word instead (先来先服务, 快表); 2–4 characters is a target, 5 is fine.
- Slots: a `[bracketed]` phrase of 1–3 words marks what the student swaps for the question's data (asset, person, data type), e.g. `Revoke [the leaked token] immediately`. Any card may use slots; keep everything outside the brackets generic (no nouns from one particular scenario), so the rest is copied unchanged.
- Abbreviation gloss: an obscure abbreviation inside a sentence may be followed by a short Chinese gloss in full-width brackets, e.g. `ECDHE（密钥协商）`, `HSTS（强制 HTTPS）`, with no space before or after the brackets (full-width brackets already carry their own white space: `use IAM（身份权限）roles`). The student skips it when copying, and `check_master.py` ignores text in （）. Add one only where it costs no line (fitting.md → Adding without a new line), and check in the PDF that it did not wrap away from its abbreviation.
- No blank lines inside a card except around tables and code fences.
- Length: 120–190 English words per card (syntax and scenario cards up to ≈ 1,400 characters; ≈ 1,600 for a card of ⑧ points that keeps a marking guide's wording).

### Mini card (★★★)

```
{W2} **★★★ 三次握手 Three-way handshake** A TCP client sends SYN, the server answers SYN-ACK and the client replies ACK, …
```

One paragraph: colour key, bold `★★★ 中文 English`, then 1–2 complete sentences (≈ 40 words, ≤ ≈ 290 non-space characters). No Q line, no tags.

### One-liner (★★)

```
{W3} **★★ SQL 子句 SQL clauses** `SELECT customer_id, SUM(amount) AS total FROM orders WHERE order_date >= '2026-01-01' GROUP BY customer_id HAVING COUNT(*) > 3 ORDER BY total DESC;` WHERE filters rows before grouping, HAVING filters groups.
```

Same shape as a mini card but one sentence (often a comparison "A …, whereas B …", a fact list for MCQs, or a code template plus one explanatory clause). Put spaces inside long inline code so Word can wrap it.

### Tables and code

- Syntax cards (selectors, query operators) may end with a compact GFM table, with a blank line before and after. Aim for ≤ 3 columns and ≤ 12 rows; 4–5 short columns (numbers, codes) still read well; anything wider goes into a code block. Tables cannot hold figures.
- Fenced code blocks (``` … ```) for multi-line examples (e.g. HTML + its DOM tree drawn with ├─ └─). The build script keeps a code block in one column and in monospace.

### Figures

Draw it as text first. A figure costs ≈ 5.3 lines per cm of height at 4.5 pt; a full-column figure with a 2 : 1 aspect ratio is ≈ 2.9 cm ≈ 15 lines, the space of 3–4 one-liners. Text diagrams are also searchable and easy to copy.

| Shape | Text version |
|---|---|
| Tree / hierarchy (DOM, nested JSON) | code block drawn with ├─ └─ |
| Flow / architecture | one line `A → B → C`, or a small code block |
| Comparison | table |
| Schema (star schema, ER) | code block listing each table with its keys |

Use an image only when the shape itself is the answer (spatial relations, chart types, an architecture you must redraw by hand):

```
![60%](figures/star-schema.png)
```

- Put it on its own line directly after what it illustrates: after the points of an answer card (like a table, and point the Q line at it: `→ ③, figure`), or right after a mini card or one-liner. A figure that does not fit at a column bottom moves to the top of the next column, away from its text; that is acceptable, or save lines above it to pull it back.
- The number in `[ ]` is the width as a percentage of the column (10–100 %, default 100 %); the height follows the aspect ratio. The path is relative to the master's folder; web URLs are not supported. Use PNG or JPG.
- Redraw rather than screenshot when you can: black line art on white, thick lines, no colours that must be told apart in greyscale. Labels must not print smaller than the body text: set their font size, in the image's own pixels, to at least ≈ 1/37 of the image width at 100 % of the column for 4.5 pt (900 px wide → 24 px), ≈ 1/22 at 60 % (for 5 pt: 1/33 and 1/20). `check_master.py --font <size>` prints the height in lines and this minimum for every image at the size you plan to print.
- Not inside tables, and not on a line with text: cell text uses exact line height, which crops images.
- When the user asks for a particular picture, use it even where the text-first rule would not; mention its cost in lines.
- Slide and textbook figures are someone else's work: keep them in your private sheet, never in a public repository.

## 3. Writing rules per question type

- **Compare A and B**: ① define A; ② define B; ③–⑤ one dimension each as "A …, whereas B …"; ⑥ "Use A when …; use B when …, e.g. …". (The review lecture's advice: define each in one sentence, then compare.)
- **Explain / why important / role**: one definition, 3–4 reasons or benefits, one example.
- **Process / steps**: one sentence per step, starting with the step name.
- **Read-the-code / syntax** (CSS selector, query operator, XPath): 3–5 rules including a worked example, then a compact table. Variant questions are answered by applying the rules; the rule sentence is the copyable justification.
- **Issue → measure**: "One issue is …; to address it, …", officially listed issues first.
- **One of each named kind** (one C, I and A requirement; a preventive, detective and recovery control): one sentence per kind that starts, after the tag, with the kind's English name and a colon (`① 机密性 Confidentiality: only [customers] may view [their orders] …`), so the marker finds each part.
- **Scenario / design framework**: Q line maps each sub-question to points; points start with the official sub-headings ("① Data Sources: …"), each a fill-in sentence whose [bracketed] parts are replaced by the question's data in the exam.
- Every sentence names its subject (no "It/This" referring back), contains no Chinese (except a （gloss） after an abbreviation), sources, page or quiz numbers, arrows or telegraphic abbreviations; code, queries and function names go in backticks.

## 4. Colour keys and palette

Line-start keys (stripped at build time): `{EXAM}` answer method, `{DESIGN}` design/scenario, `{W1}`…`{W12}` twelve further palette colours (named after lecture weeks, but they are only colour names). Any other `{…}` at the start of a line is printed as it is.

Give a mini card or one-liner the same key as the answer cards of its topic: with the default mapping below, topic 1 → `{W2}`, topic 2 → `{W3}` and so on, so `{W1}` is not "topic 1". For a new course it is simplest to put `配色: 1=W1 2=W2 3=W3 …` in the header notes, so that topic n is `{Wn}`.

Answer cards take their colour from the 〔topic〕 in the title: A→EXAM, 1→W2, 2→W3, 3→W4, 4→W5, 5→W6, 6→W7, 7→W8, 8→W9, 9→W10, 10→W12; any other number cycles through W1…W12 (11→W11, 13→W1). For another course, put one line in the header notes such as `配色: 1=W3 2=W5 B=DESIGN` (also accepted: `colours:`); its pairs override the defaults. A topic that is neither a number nor in that line (e.g. 〔B〕 without a mapping) gets grey, and `check_master.py` reports it.

| Key | Hex | Key | Hex | Key | Hex |
|---|---|---|---|---|---|
| EXAM | 1F3B57 | W3 | 1565C0 | W8 | 6D4C41 |
| DESIGN | 8D6E00 | W4 | D84315 | W9 | 283593 |
| W1 | 546E7A | W5 | 6A1B9A | W10 | 37474F |
| W2 | 2E7D32 | W6 | 00838F | W11 | 558B2F |
|  |  | W7 | AD1457 | W12 | C62828 |

Tint (table header fill) = 14 % of the colour mixed with white.

## 5. Printed layout (implemented by `build_cheatsheet.py`)

- A4 landscape, margins 0 (argument 4 for cm), 5 newspaper columns, 0.1 cm gap (argument 5 for cm; 0.05 still keeps text off the rule, 0 does not) with a separator rule.
- The document is marked as Word 2013+ (`compatibilityMode` 15); without it Word lays out in compatibility mode and rounds letter positions to 96-dpi pixels.
- Every paragraph: exact line height 1.18 × size, normal letter spacing, left aligned, no space before/after, widow/orphan control off (otherwise columns end with empty lines). Leading ★ marks are stripped from the printed text.
- The card title and the Q line are not split across columns when they wrap to two lines, but a column may end right after either of them: the card goes on at the top of the next column, so no lines are left empty at column bottoms. Build with `--keep-with-next` to keep title + Q line + first point in one column instead. A code block is kept in one column. Title bars are indented 2 pt on both sides, because Word's paragraph shading reaches ≈ 1.7 pt beyond the text and would otherwise cross the separator.
- Hanging indent: points ≈ 1.05 × size; mini cards and one-liners ≈ 1.6 × size.
- Tables: 100 % width, 0.25 pt grey (808080) borders, ≈ 0.05 cm cell padding.
- Figures: their own paragraph with single line height (exact line height would crop them to one line), scaled to the given percentage of the column width, never split across columns.

### Font and style table 字体样式表

Everything is printed at **one size** (argument 3: default 4.5 pt, print-tested; 5 pt for larger print) with exact line height 1.18 × size (4.5 pt → 5.3 pt, 5 pt → 5.9 pt). There are no larger headings: the hierarchy comes only from fill, colour and bold. "Topic colour" is the card's palette colour (§4), and "tint" is 14 % of that colour mixed with white.

| Element 元素 | Written as | Latin font | CJK font | Weight | Text colour | Background |
|---|---|---|---|---|---|---|
| Body text 正文 | plain text | Segoe UI | 微软雅黑 | regular | black | none |
| Bold in text 正文加粗 | `**…**` | Segoe UI | 微软雅黑 | bold | black | none |
| Answer-card title 答题卡标题 | `**★★★★ …**` | Segoe UI | 微软雅黑 | regular (bold with `--bold-titles`) | white | topic-colour bar |
| Q line / 用法 line 题干行 | `Q: …` / `用法…` | Segoe UI | 微软雅黑 | regular | dark grey 404040 | none |
| Point tag 要点标签 | `①` + Chinese tag | Segoe UI | 微软雅黑 | number regular (bold with `--bold-titles`), tag bold | topic colour | none |
| Point sentence 要点句 | text after the tag | Segoe UI | 微软雅黑 | regular | black | none |
| Mini-card / one-liner title 精简卡、单句标题 | `**★★★ …**` / `**★★ …**` | Segoe UI | 微软雅黑 | bold | topic colour | none |
| Table header 表头 | first table row | Segoe UI | 微软雅黑 | bold | topic colour | topic tint |
| Table cells 表格内容 | other rows | Segoe UI | 微软雅黑 | regular | black | none |
| Inline code 行内代码 | `` `…` `` | Arial Narrow | 微软雅黑 | regular | black | none |
| Code block 代码块 | fenced block | Consolas | 微软雅黑 | regular | black | light grey F2F2F2 |
| Figure 图片 | `![60%](fig.png)` | – | – | – | – | none (scaled to 60 % of the column, single line height) |

- A card without a colour gets a light-grey (E2E2E2) title bar and table header, with black text.
- Why these fonts: Segoe UI is about as compact as condensed Arial but its letters stay distinct at 4.5–5 pt; Arial Narrow keeps long inline code short; Consolas is monospaced, which DOM trees and aligned code need.
- The fonts are set in one line of `build_cheatsheet.py` (`LATIN, EA, MONO, NARROW = …`). If a font is missing (for example on a Mac without Microsoft fonts), Word substitutes another one silently and the page count changes, so change that line (e.g. Helvetica Neue / PingFang SC / Menlo / Arial Narrow), rebuild, and measure again.

## 6. Capacity and self-check

- Capacity at 4.5 pt ≈ 4,800 non-space characters per column, ≈ 48,000 for both sides; 5 pt holds ≈ 20 % less (≈ 4,000 / 40,000).
- Before building, run `scripts/check_master.py`. It checks what a script can: card titles bold and coloured, colour keys known, a Q line under every answer card, point numbering continuous, every Q reference pointing to an existing point (and a reminder for each point no Q cue points to, since it cannot be found from a question), tags recognised; in every copyable sentence (answer-card points, mini cards, one-liners) no Chinese inside the English (text in full-width （） is ignored), no opening with It/This/These/They, no source words (lecture, slide, tutorial, textbook, quiz, Week 3, W3, p. 4, page 4) and no `[slot]` longer than 5 words; image files present (with each figure's height in lines), and lengths (Q line ≤ 25 words, point ≤ 40 words, answer card ≤ 1,600, mini card ≤ 290, one-liner ≤ 400 non-space characters). Its limits are deliberately a little looser than the targets above. It ends with how many sentences are copied as they are and how many carry a slot.
- Still check by hand: each sample-exam part's official points are in the first points of one card, the Q lines point to the *right* points, every slot is something the question supplies, and the PDF has at most two pages (exactly two when the material fills them).
