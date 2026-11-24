# Companion documents

Optional documents around the sheet: a practice paper to rehearse copying from it, and handouts for what the student memorises instead of looking up. Write them in Markdown next to the master and print them with `scripts/md_to_pdf.py` (end of this file). Write the questions yourself in the exam's style; never copy the official mock's or the question bank's wording, and say in the document that they are not real exam questions.

## Contents
1. Practice paper and answer key
2. MCQ handout
3. Review handout
4. Making the PDFs

## 1. Practice paper and answer key

Paper: the real exam's sections, marks and language, with new scenarios. Besides questions that one card answers, include the two kinds a sheet alone does not answer:
- **one scenario across several topics**: each sub-question needs a different card;
- **compare, prioritise, evaluate or "who must be informed"**: card sentences plus one short sentence of the student's own that states the comparison, the order or the conclusion.

Answer key, for each sub-question:
- **定卡**: card name, points and position from `measure_layout.py sheet.pdf --cards sheet.md`, e.g. `隐私与治理 ②（B 面第 2 栏 84%）`;
- **参考答案**, each sentence labelled with how it was made:

| Label | Meaning |
|---|---|
| 【原样】 | a card sentence copied unchanged |
| 【换槽】 | only the `[slot]` words changed to the question's |
| 【题干句】 | a sentence built from the question's own words |
| 【自写一句】 | a short sentence that is not on the sheet, joined with *whereas*, *comes first because*, *but … so …* or *should be informed because* |

A sub-question that needs several 【自写一句】 shows a gap: add the sentence to its card, or record it in the gap list. For MCQs, a table of answer, why and where it is on the sheet (or "not on the sheet: MCQ handout"). Write at the top which build the positions refer to, and rerun `--cards` after every layout change.

## 2. MCQ handout

When MCQs are memorised rather than looked up (the sheet then holds scenario answers only), a handout replaces the MCQ one-liners:

0. Method: how to read a stem (which security goal or concept is tested, qualifier words such as *primarily*, *first*, *best*, eliminating options); use the review lecture's advice when it gives one.
1. Per topic: 知识点 → 易错点 → worked examples. Examples in the exam's language; answer and explanation in the student's language, with the English terms kept.
2. A self-test of ≈ 15 questions, answers at the end.
3. A one-page trap table to read in the last minutes before the exam.

Follow the course's own version of a fact where it differs from other sources, and say so.

## 3. Review handout

A topic-by-topic summary in the student's language. Sections that proved useful:
1. How to spend the time left before the exam.
2. Exam format and how marks are given.
3. One-page overview of the course.
4. Topic-by-topic notes (key terms in English).
5. Comparisons across topics to memorise.
6. Answering method with one worked example.
7. Self-check list.

## 4. Making the PDFs

```bash
python <skill>/scripts/md_to_pdf.py handout.md paper.md key.md        # PDFs next to the .md files
```

pandoc turns each file into HTML styled by `assets/handout.css` (A4, Segoe UI + 微软雅黑; tables, blockquotes and list items not split across pages), then Chrome or Edge prints it to PDF without header or footer. Single line breaks are kept and a list may follow a paragraph without a blank line. Needs pandoc (found as for the build) and Chrome or Edge (or set `CHROME` to the browser's path). Close a PDF in the viewer before rebuilding it.
