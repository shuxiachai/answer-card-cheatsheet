"""抄写演练：只用 cheatsheet 上的原句、只换 [ ] 里的词，把官方模拟卷或题库的每个小问答一遍。

用法：
    python rehearse.py 你的cheatsheet.md 题目清单.md [--out 演练.md] [--pdf 你的cheatsheet.pdf --gap-cm 0.1]

题目清单是自己写的 Markdown（范例：assets/example_rehearsal.md）：
    ## 卷名                          一份模拟卷，或题库里的一个案例
    ### a) 小问的题干                 题干保留题目自己的英文词，用来查标题里找不找得到
    卡: 卡名 ①②④ | [槽里原来的词] = 换成的词 | [另一个槽] = …
    卡: 另一张卡 ⑤                   一个小问可以用几张卡；精简卡和二星单句不写序号
    自写: 表上没有、要自己写的一句（比较、排序、结论）
    注: 给自己的提醒（可选）
    答案: 官方答案的给分点，用来对照（可选）
卡名写标题开头的中文名就行（例如「TCP 与 UDP」），不用写〔主题〕和英文关键词。也可以用英文字段名
card: / own: / note: / guide:。其他行（说明、空行）都不读。

每个小问：
- 拼出要抄的句子：（中文注）去掉，[ ] 换成清单给的词；没给的槽沿用槽里原来的词，并单独列出来提醒。
- 检查：卡和序号都存在、清单里写的槽在句子里找得到（不然是错误）；序号在 Q 行里（Q 行没指到，考场上按 Q 行
  抄会漏掉）；题干里的英文词在这张卡的标题里能找到几个（少于 2 个不好找），别的卡标题里是不是找到得更多
  （考场上可能先翻到那张）。
- 结论：✅ 只换槽；✅ 加一句自写；🟡 要自写两句以上（把句子补进卡里，或记进 gap list）；❌ 清单有错。
最后列出没有任何小问用到的要点和卡：清单覆盖了全部练习题时，它们是挤版时先考虑删的候选（删前先问学生）。
--out  把演练写成 Markdown：每个小问的找卡、抄哪几条、拼好的答案、换了哪些槽，可以用 md_to_pdf.py 打印。
--pdf  给出排好的 PDF 时，抄哪几条后面加上卡片开头的位置（A2 35% = A 面第 2 栏、从栏顶往下 35%）；
       --gap-cm 和排版时一致。版面改了以后，用
       measure_layout.py 排好的.pdf --cards 母版.md --update 演练.md 刷新这些位置。
有错误时退出码为 1。
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser(description="只用 cheatsheet 原句、只换槽，把练习题的每个小问答一遍")
ap.add_argument("master", help="Markdown 母版")
ap.add_argument("spec", help="题目清单（Markdown）")
ap.add_argument("--out", help="把演练写成这个 Markdown 文件")
ap.add_argument("--pdf", help="排好的 PDF：在抄哪几条后面加上卡片位置")
ap.add_argument("--gap-cm", type=float, default=0.1, help="栏间距（cm），和排版时一致，默认 0.1；只在给了 --pdf 时用")
args = ap.parse_args()

# 和 check_master.py 一致
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫"
CARD_RE = re.compile(r"^(?:\{[^}]*\}\s*)?\*\*(★★★★|★★★ |★★ )\s*(.*?)\*\*\s*(.*)$")
TAG_RE = re.compile(r"^([" + CIRCLED + r"]\s*(?:[^\sA-Za-z(\[`]+|[A-Z][A-Za-z]*(?: [A-Za-z]+){0,2}:)\s)")
RANGE_RE = re.compile(r"([" + CIRCLED + r"])\s*[–—\-~～]\s*([" + CIRCLED + r"])")
MIN_HITS = 2              # 题干词在标题里少于这么多个，考场上不好找

# 和 source_audit.py 一致：词的变形都算同一个词
STOP = set("""a about above after again against all also although am an and any are as at be because been before
being below between both but by can could did do does doing done down during each either else enough even every
for from further had has have having he her here hers him his how however i if in into is it its itself just
least less let like may might more most much must my no nor not now of off often on once one only or other our
ours out over own per rather same she should since so some such than that the their theirs them then there these
they this those though through thus to too two under until up upon us very via was we were what when where whether
which while who whom whose why will with within without would yet you your whereas whilst hence therefore thereby
instead unless besides toward towards across along around among amongst behind beyond onto inside outside already
still never always explain describe discuss identify outline briefly give provide suggest propose list state three
four five question answer marks scenario case""".split())
SPELLING = {"licence": "license", "licences": "licenses", "defence": "defense", "offence": "offense",
            "practise": "practice", "programme": "program", "programmes": "programs"}
SUFFIXES = (("ies", "y"), ("ied", "y"), ("ily", "y"), ("es", ""), ("s", ""), ("ed", ""), ("ed", "e"), ("ing", ""),
            ("ing", "e"), ("ly", ""), ("er", ""), ("er", "e"), ("est", ""), ("est", "e"), ("ations", ""),
            ("ations", "e"), ("ation", ""), ("ation", "e"), ("ment", ""), ("ments", ""), ("ness", ""))


def forms(w):
    w = w.lower().strip("-'")
    if w.endswith("'s"):
        w = w[:-2]
    w = SPELLING.get(w, w)
    w = re.sub(r"is(e|es|ed|ing|ation|ations|er|ers)$", r"iz\1", w)
    if len(w) >= 6:
        w = re.sub(r"our(s|ed|ing|al)?$", r"or\1", w)
    out = {w}
    for suf, add in SUFFIXES:
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            b = w[:-len(suf)] + add
            out.add(b)
            if len(b) >= 4 and b[-1] == b[-2] and b[-1] not in "aeiouls":
                out.add(b[:-1])
    return out


def keywords(text):
    """{小写词: 它的各种变形}，不算虚词、题目常用的动词和 [ ] 里的词；连字符词也按各部分算。"""
    out = {}
    for w in re.findall(r"[A-Za-z][A-Za-z'\-]*[A-Za-z]|[A-Za-z]", re.sub(r"\[[^\]]*\]", " ", text)):
        low = w.lower()
        if low in STOP or (len(w) < 3 and not w.isupper()):
            continue
        f = set(forms(low))
        for part in low.split("-"):
            if len(part) >= 3 and part not in STOP:
                f |= forms(part)
        out[low] = f
    return out


def expand(s):
    """「①–③⑥」→ [1, 2, 3, 6]"""
    nums = []
    for a, b in RANGE_RE.findall(s):
        nums += range(CIRCLED.index(a) + 1, CIRCLED.index(b) + 2)
    nums += [CIRCLED.index(c) + 1 for c in RANGE_RE.sub(" ", s) if c in CIRCLED]
    return sorted(set(nums))


def circ(nums):
    return "".join(CIRCLED[n - 1] for n in nums)


# ---- 1. 母版：每张卡的标题、Q 行、要点；精简卡和二星单句的句子 ----------------------------------------------
text = "\n" + Path(args.master).read_text(encoding="utf-8").replace("\r\n", "\n")
offset = 0
if "\n## 答题卡\n" in text:
    head, text = text.split("\n## 答题卡\n", 1)
    offset = head.count("\n") + 2
blocks, cur, fence = [], None, False
for ln, line in enumerate(text.split("\n"), start=offset):
    if line.startswith("```"):
        fence = not fence
        continue
    if fence:
        continue
    cm = CARD_RE.match(line)
    if cm:
        title = cm.group(2).strip()
        cur = {"kind": cm.group(1).strip(), "title": title, "line": ln, "q": "", "points": {}, "body": cm.group(3),
               "name": re.sub(r"^〔[^〕]*〕\s*", "", title.replace("`", "")).strip()}
        blocks.append(cur)
        continue
    if cur is None or cur["kind"] != "★★★★":
        continue
    if line.startswith(("Q:", "用法")) and not cur["q"] and not cur["points"]:
        cur["q"] = line
    elif line and line[0] in CIRCLED:
        tm = TAG_RE.match(line)
        cur["points"][CIRCLED.index(line[0]) + 1] = line[tm.end():].strip() if tm else line[1:].strip().split(" ", 1)[-1]
if not blocks:
    sys.exit("母版里没有找到卡片（标题行要以 **★★★★ / **★★★ / **★★ 开头）")
for b in blocks:
    b["keys"] = set().union(*keywords(b["name"]).values())
    b["routed"] = set(expand(b["q"])) if b["q"].startswith("Q:") else None


def find_block(name):
    hits = [b for b in blocks if b["name"] == name or b["name"].startswith(name + " ")]
    exact = [b for b in hits if b["name"] == name]
    return exact or hits


def short(b):
    """答题卡标题开头的中文名，用在提示里：到第一个小写英文词、或重复出现的英文词为止（「TCP 与 UDP TCP vs …」）。"""
    if b["kind"] != "★★★★":
        return b["name"][:24]
    out = []
    for t in b["name"].split():
        if t[0] in "abcdefghijklmnopqrstuvwxyz·" or (t.isascii() and t in out):
            break
        out.append(t)
    return " ".join(out) or b["name"][:24]


# ---- 2. 卡片位置（可选）：借 measure_layout.py --cards 的输出 -------------------------------------------------
positions = {}
if args.pdf:
    out = subprocess.run([sys.executable, str(Path(__file__).with_name("measure_layout.py")), args.pdf,
                          "--cards", args.master, "--gap-cm", str(args.gap_cm)],
                         capture_output=True, text=True, encoding="utf-8")
    if out.returncode:
        sys.exit("measure_layout.py 出错：\n" + out.stderr)
    for row in out.stdout.splitlines():     # "  A2  35% → A3 ★★★★ 〔1 价值〕 …"（标题只印前 50 个字）
        pm = re.match(r"^  ([A-G]\d)\s+(\d+)%(?: → [A-G]\d)?\s+(★{2,4})\s*(.*?)\s*$", row)
        if pm:
            positions[(pm.group(3), pm.group(4))] = f"{pm.group(1)} {pm.group(2)}%"


def position(b):
    p = positions.get((b["kind"], b["title"][:50].strip()))
    return f"（{p}）" if p else ""


# ---- 3. 题目清单 --------------------------------------------------------------------------------------------
FIELD_RE = re.compile(r"^(卡|自写|注|答案|card|own|note|guide)\s*[:：]\s*(.*)$", re.I)
papers, q = [], None
for ln, raw in enumerate(Path(args.spec).read_text(encoding="utf-8").replace("\r\n", "\n").split("\n"), start=1):
    line = raw.strip()
    if line.startswith("### "):
        q = {"id": line[4:].strip(), "line": ln, "picks": [], "own": [], "note": "", "guide": ""}
        if not papers:
            papers.append(["", []])
        papers[-1][1].append(q)
    elif line.startswith("## "):
        papers.append([line[3:].strip(), []])
        q = None
    elif q is None or not line:
        continue
    else:
        fm = FIELD_RE.match(line)
        if not fm:
            continue
        field, value = fm.group(1).lower(), fm.group(2).strip()
        if field in ("卡", "card"):
            q["picks"].append((ln, value))
        elif field in ("自写", "own"):
            q["own"].append(value)
        elif field in ("注", "note"):
            q["note"] = value
        else:
            q["guide"] = value
questions = [q for _, qs in papers for q in qs]
if not questions:
    sys.exit("题目清单里没有小问（每个小问以 ### 开头）")


def norm(s):
    return " ".join(s.split()).lower()


def fill(sentence, mapping, used, kept):
    """去掉（中文注），把 [槽] 换成清单给的词（加粗）；没给的槽沿用原词，记进 kept。"""
    s = re.sub(r"（[^）]*）(?=[A-Za-z0-9])", " ", sentence)
    s = re.sub(r"（[^）]*）", "", s)

    def rep(m):
        k = norm(m.group(1))
        if k in mapping:
            used.add(k)
            v = mapping[k][1]
            return m.group(1) if v is None or norm(v) == k else f"**{v}**"
        kept.append(m.group(1))
        return m.group(1)
    return re.sub(r"\[([^\]]+)\]", rep, s)


# ---- 4. 逐个小问 ---------------------------------------------------------------------------------------------
used_points = {id(b): set() for b in blocks}
errors = 0
for q in questions:
    q["errors"], q["warns"], q["sentences"], q["copy"], q["swaps"], q["kept"], q["cards"] = [], [], [], [], [], [], []
    q["names"] = {}
    for ln, pick in q["picks"]:
        parts = [p.strip() for p in pick.split("|")]
        i = next((k for k, ch in enumerate(parts[0]) if ch in CIRCLED), len(parts[0]))
        name, nums = parts[0][:i].strip(), expand(parts[0][i:])
        hits = find_block(name)
        if len(hits) != 1:
            q["errors"].append(f"清单第 {ln} 行：" + (f"找不到卡「{name}」" if not hits else
                               f"「{name}」对上 {len(hits)} 张卡（{'；'.join(b['name'][:24] for b in hits)}），写长一点"))
            continue
        b = hits[0]
        q["cards"].append(b)
        q["names"][id(b)] = name
        mapping = {}
        for p in parts[1:]:
            sm = re.match(r"^\[\s*(.+?)\s*\]\s*(?:=\s*(.*))?$", p)
            if not sm:
                q["errors"].append(f"清单第 {ln} 行：看不懂「{p}」（槽写成 [原词] = 新词）")
                continue
            mapping[norm(sm.group(1))] = (sm.group(1), sm.group(2).strip() if sm.group(2) else None)
        if b["kind"] == "★★★★":
            if not nums:
                q["errors"].append(f"清单第 {ln} 行：答题卡「{short(b)}」要写抄第几条")
                continue
            missing = [n for n in nums if n not in b["points"]]
            if missing:
                q["errors"].append(f"清单第 {ln} 行：「{short(b)}」没有 {circ(missing)}")
                continue
            texts = [b["points"][n] for n in nums]
            used_points[id(b)].update(nums)
            if b["routed"] is not None and set(nums) - b["routed"]:
                q["warns"].append(f"Q 行没指到 {short(b)} {circ(sorted(set(nums) - b['routed']))}"
                                  "：考场上按 Q 行抄会漏掉，把它加进 Q 行")
        elif nums:
            q["errors"].append(f"清单第 {ln} 行：「{short(b)}」是精简卡或二星单句，没有序号，去掉 {circ(nums)}")
            continue
        else:
            texts = [b["body"]]
        used = set()
        q["sentences"] += [fill(t, mapping, used, q["kept"]) for t in texts]
        q["swaps"] += [f"[{o}] → {v}" for k, (o, v) in mapping.items() if v is not None and norm(v) != k and k in used]
        for k in sorted(set(mapping) - used):
            q["errors"].append(f"清单第 {ln} 行：「{short(b)}」{circ(nums)} 里没有槽 [{mapping[k][0]}]")
        if q["copy"] and q["copy"][-1][0] is b:     # 同一张卡接着写的几行并成一项：「卡名 ③④⑤」
            q["copy"][-1][2] += nums
        else:
            q["copy"].append([b, name, list(nums)])
    q["copy"] = [name + (" " + circ(nums) if nums else "") + position(b)    # 抄两遍的条目写两次：①②②④
                 for b, name, nums in q["copy"]]
    # 找卡：题干里的英文词在标题里找到几个
    stem = re.sub(r"^\(?[A-Za-z0-9]{1,3}[).]\s*", "", q["id"])
    keys = keywords(stem)
    q["found"] = None
    if keys and q["cards"]:
        def score(b):
            return [w for w, f in keys.items() if f & b["keys"]]
        best = max(q["cards"], key=lambda b: len(score(b)))
        hit = score(best)
        q["found"] = (best, hit)
        if len(hit) < MIN_HITS:
            q["warns"].append(f"题干词在「{q['names'][id(best)]}」的标题里只找到 {len(hit)} 个"
                              f"{'（' + ', '.join(hit) + '）' if hit else ''}：把题干的说法加进标题")
        others = sorted(((len(score(b)), b) for b in blocks if b["kind"] == "★★★★" and b not in q["cards"]),
                        key=lambda x: -x[0])
        if others and others[0][0] > len(hit):
            q["warns"].append(f"题干词在「{short(others[0][1])}」的标题里找到 {others[0][0]} 个，"
                              f"比要抄的卡多：考场上可能先翻到那张")
    if q["errors"]:
        q["verdict"] = "❌ 清单有错"
        errors += 1
    elif not q["own"]:
        q["verdict"] = "✅ 只换槽"
    elif len(q["own"]) == 1:
        q["verdict"] = "✅ 加一句自写"
    else:
        q["verdict"] = f"🟡 自写 {len(q['own'])} 句"

# ---- 5. 报告 ------------------------------------------------------------------------------------------------
tally = {}
for q in questions:
    v = q["verdict"].split(" ", 1)[1] if q["verdict"][0] != "🟡" else "自写两句以上"
    tally[v] = tally.get(v, 0) + 1
order = ["只换槽", "加一句自写", "自写两句以上", "清单有错"]
summary = "，".join(f"{v} {tally[v]} 问" for v in order if v in tally)
print(f"{len(questions)} 个小问：{summary}")
for title, qs in papers:
    if title:
        print(f"== {title}")
    for q in qs:
        print(f"  {q['verdict'][:1]} {q['id'][:60]}")
        for e in q["errors"]:
            print(f"      [错误] {e}")
        for w in q["warns"]:
            print(f"      [提醒] {w}")
        if q["kept"]:
            print(f"      [沿用槽内原词] " + "、".join(f"[{k}]" for k in dict.fromkeys(q["kept"])))
        if len(q["own"]) > 1:
            print(f"      [自写] {len(q['own'])} 句：把句子补进卡里，或记进 gap list")

unused, idle = [], []
for b in blocks:
    if b["kind"] != "★★★★":
        continue
    rest = sorted(set(b["points"]) - used_points[id(b)])
    if len(rest) == len(b["points"]):
        idle.append(b)
    elif rest:
        unused.append((b, rest))
n_pts = sum(len(b["points"]) for b in blocks if b["kind"] == "★★★★")
n_unused = sum(len(r) for _, r in unused) + sum(len(b["points"]) for b in idle)
print(f"没有小问用到的要点 {n_unused} 条（答题卡共 {n_pts} 条）；清单覆盖了全部练习题时，挤版先考虑这些（删前先问学生）：")
for b, rest in unused:
    print(f"  第 {b['line']} 行 {short(b)} {circ(rest)}")
if idle:
    print(f"没有小问用到的卡 {len(idle)} 张：" + "；".join(short(b) for b in idle))

if args.out:
    md = [f"# 抄写演练\n", f"答案全部由 `{Path(args.master).name}` 的原句拼成，只换 [ ] 里的词；**加粗**的是换进槽里的词，"
          "（中文注）不抄。题目清单：" + f"`{Path(args.spec).name}`。\n",
          f"结果：{summary}。✅ 只换槽或加一句自写就能答完；🟡 要自写两句以上；❌ 清单有错。\n"]
    if positions:
        md.append(f"卡片位置按 `{Path(args.pdf).name}`（A2 35% = A 面第 2 栏、从栏顶往下 35%）。版面改了以后用 "
                  f"`measure_layout.py {Path(args.pdf).name} --cards {Path(args.master).name} --update "
                  f"{Path(args.out).name}` 刷新。\n")
    for title, qs in papers:
        if title:
            md.append(f"\n## {title}\n")
        for q in qs:
            md.append(f"### {q['id']} {q['verdict']}\n")
            if q["found"]:
                b, hit = q["found"]
                md.append(f"**找卡：** {q['names'][id(b)]} — 标题里有 {len(hit)} 个题干词"
                          + (f"：{', '.join(hit)}" if hit else "") + "\n")
            if q["copy"]:
                md.append("**抄：** " + " ＋ ".join(q["copy"]) + "\n")
            body = " ".join(q["sentences"] + [f"*【自写】{o}*" for o in q["own"]])
            if body:
                md.append("> " + body + "\n")
            line = "**换槽：** " + ("；".join(dict.fromkeys(q["swaps"])) or "无")
            if q["kept"]:
                line += "。沿用槽内原词：" + "、".join(f"[{k}]" for k in dict.fromkeys(q["kept"]))
            md.append(line + "\n")
            for e in q["errors"]:
                md.append(f"❌ {e}\n")
            for w in q["warns"]:
                md.append(f"⚠ {w}\n")
            if q["note"]:
                md.append(f"**注：** {q['note']}\n")
            if q["guide"]:
                md.append(f"**答案要点：** {q['guide']}\n")
    md.append(f"\n## 没有小问用到的要点\n")
    md.append(f"共 {n_unused} 条（答题卡共 {n_pts} 条）。清单覆盖了全部练习题时，挤版先考虑这些；删前先和学生确认。\n")
    md += [f"- {short(b)} {circ(rest)}" for b, rest in unused]
    if idle:
        md.append("- 整张没用到：" + "；".join(short(b) for b in idle))
    Path(args.out).write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"演练写到 {args.out}")
sys.exit(1 if errors else 0)
