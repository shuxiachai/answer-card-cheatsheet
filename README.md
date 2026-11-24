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

## 使用方法

适合「限定开卷、只能带一张 A4 双面」的考试：把可能考的题做成答题卡，考场上找到卡就能整句抄英文答案。

1. **准备资料**（放进项目文件夹，或告诉 Claude 在哪里）
   - 考试规则：几张纸、单面还是双面、题型和分值。
   - 复习课、官方模拟卷和答案或评分指南、题库：最重要，卡片句子尽量用评分指南里的关键词。
   - 各周课件（特别是 Summary 页）、tutorial、quiz。
   - 同学的 cheatsheet 只用来查漏，不照抄。
2. **说清要求**，例如「只用来答场景题，选择题我另外背」「不要留白」。
3. **Claude 会做的**
   - 每道可能的考题一张答题卡：标题是中文名加题目里会出现的英文关键词；Q 行写问法和要抄第几条；每条要点是一句完整的英文，约 1 分。
   - 要按题目换的词放在 `[ ]` 里；生僻缩写后面可以加（中文注），抄的时候跳过。
   - 排成 A4 横向 5 栏、正好两页，生成 `.md`（母版）、`.docx` 和 `.pdf`。
4. **你要检查的**
   - 每句能不能直接抄，有没有看不懂的缩写。
   - 拿官方模拟卷和题库演练一遍：每个小问都能在表上找到要抄的句子，找不到的让 Claude 补。
   - 想多练可以让 Claude 出模拟卷和答案：答案标出每句抄自哪张卡（【原样】【换槽】【题干句】【自写一句】）。选择题不放在表上时，可以另做一份选择题讲义，考前背熟。
   - 改内容时让 Claude 改 `.md`，不要直接改 `.docx`。
5. **打印**：打印 PDF（版面固定），不要换一台电脑重新打开 `.docx` 再打。默认 4.5 pt，实际考试中打印出来看得清；先打一份确认，看不清就改成 5 pt。
6. **考场上**：读题 → 用题目里的英文关键词找卡片标题 → 看 Q 行指向第几条 → 整句抄，只换 `[ ]` 里的词，（）里的中文注不抄。一道题跨好几个主题时按小问分别找卡；遇到 compare / prioritise / evaluate，在原句后面补一句自己的话，点明比较、先后或结论。

## Requirements

- Python 3 with `python-docx` and `PyMuPDF` (`pip install python-docx pymupdf`)
- `pandoc` 2.x or newer: on PATH, named by the `PANDOC` environment variable, or the copy bundled with RStudio / Quarto (found automatically)
- Microsoft Word on Windows for `scripts/export_pdf.ps1` (or export the `.docx` to PDF any other way)
- Google Chrome or Microsoft Edge for `scripts/md_to_pdf.py` (companion documents only)

## Contents

| Path | What it is |
|---|---|
| `SKILL.md` | Workflow: collect exam signals, tier the content, write the master, build, fit to two pages, verify, rehearse with a mock exam |
| `references/format.md` | Exact Markdown syntax of every block, writing rules per question type, colour palette, layout spec |
| `references/fitting.md` | How to land on two pages: column-bottom gaps, measured compression ladder, too little content, trimming, pitfalls |
| `references/companions.md` | Optional practice paper and answer key (every sentence labelled by how it was made), MCQ handout, review handout |
| `scripts/check_master.py` | Checks the master before building (colours, Q-line references, numbering, tags, lengths, figures) and every copyable sentence (Chinese, It/This openings, source words, slot length); counts sentences with and without `[slots]` |
| `scripts/build_cheatsheet.py` | Markdown master → `.docx` (`python build_cheatsheet.py sheet.md [out.docx] [font_pt=4.5] [margin_cm=0] [gap_cm=0.1]`); figures via `![60%](fig.png)` |
| `scripts/export_pdf.ps1` | Word export of the `.docx` to PDF (relative or absolute paths); uses Microsoft Print to PDF for its own Word session so small text is evenly spaced |
| `scripts/measure_layout.py` | Page count, spare lines, uneven letter spacing, short last lines, where given text sits, and with `--cards sheet.md` where every card starts (font size and margin detected from the PDF) |
| `scripts/md_to_pdf.py` | Markdown → PDF for companion documents (pandoc → HTML → Chrome/Edge print) |
| `assets/handout.css` | A4 style for those PDFs |
| `assets/example.md` | A short made-up master (Computer Networks) showing the format |
