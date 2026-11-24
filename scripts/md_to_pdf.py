"""把配套文件（复习讲义、选择题讲义、模拟卷、答案）从 Markdown 转成 PDF。

用法：
    python md_to_pdf.py 讲义.md [模拟卷.md 答案.md ...] [--css 样式.css] [--out-dir 文件夹]
流程：pandoc 把每个 .md 转成一页独立的 HTML（样式用 assets/handout.css：A4、Segoe UI + 微软雅黑，
表格、引用块和列表项不跨页拆开），再用 Chrome 或 Edge 无界面打印成 PDF（不带页眉页脚）。
单个换行会保留（hard_line_breaks），列表前面不空行也能识别，和手写笔记的习惯一致；$ 不当作公式。
PDF 默认放在 .md 旁边、同名；--out-dir 可以换文件夹。
pandoc 的查找顺序和 build_cheatsheet.py 一样（环境变量 PANDOC → PATH → RStudio / Quarto 自带的那份）；
浏览器：环境变量 CHROME → PATH → Chrome / Edge 的常见安装位置。
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser(description="Markdown → PDF（pandoc + Chrome/Edge），用于讲义、模拟卷和答案")
ap.add_argument("md", nargs="+", help="一个或多个 Markdown 文件")
ap.add_argument("--css", default=str(HERE.parent / "assets" / "handout.css"), help="样式表，默认 assets/handout.css")
ap.add_argument("--out-dir", help="PDF 放在哪个文件夹（默认和 .md 同一个文件夹）")
args = ap.parse_args()


def find_pandoc():
    """pandoc 的位置：环境变量 PANDOC → PATH → RStudio / Quarto / Pandoc 的常见安装位置。"""
    env = os.environ.get("PANDOC")
    if env and Path(env).is_file():
        return env
    if shutil.which("pandoc"):
        return shutil.which("pandoc")
    if os.name == "nt":
        rel = ["Program Files/RStudio/resources/app/bin/quarto/bin/tools/pandoc.exe",
               "Program Files/RStudio/resources/app/bin/pandoc/pandoc.exe",
               "Program Files/RStudio/bin/quarto/bin/tools/pandoc.exe",
               "Program Files/RStudio/bin/pandoc/pandoc.exe",
               "Program Files/Quarto/bin/tools/pandoc.exe",
               "Program Files/Pandoc/pandoc.exe"]
        cands = [f"{d}:/{r}" for d in "CDEFGH" for r in rel]
        local = os.environ.get("LOCALAPPDATA", "")
        cands += [f"{local}/Pandoc/pandoc.exe", f"{local}/Programs/Quarto/bin/tools/pandoc.exe",
                  f"{local}/Programs/RStudio/resources/app/bin/quarto/bin/tools/pandoc.exe"]
    else:
        tools = ["/Applications/RStudio.app/Contents/Resources/app/quarto/bin/tools",
                 "/Applications/quarto/bin/tools", "/opt/quarto/bin/tools",
                 "/usr/lib/rstudio/resources/app/bin/quarto/bin/tools", "/usr/lib/rstudio/bin/quarto/bin/tools"]
        cands = [f"{t}/{arch}pandoc" for t in tools for arch in ("", "aarch64/", "x86_64/")]
    return next((c for c in cands if Path(c).is_file()), None)


def find_browser():
    """Chrome 或 Edge：环境变量 CHROME → PATH → 常见安装位置。"""
    env = os.environ.get("CHROME")
    if env and Path(env).is_file():
        return env
    for name in ("chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "msedge",
                 "microsoft-edge"):
        if shutil.which(name):
            return shutil.which(name)
    cands = []
    for var in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        base = os.environ.get(var)
        if base:
            cands += [f"{base}/Google/Chrome/Application/chrome.exe", f"{base}/Microsoft/Edge/Application/msedge.exe"]
    cands += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
    return next((c for c in cands if Path(c).is_file()), None)


PANDOC, BROWSER = find_pandoc(), find_browser()
if PANDOC is None:
    sys.exit("找不到 pandoc：安装 pandoc（https://pandoc.org），或把环境变量 PANDOC 设成 pandoc 的完整路径。")
if BROWSER is None:
    sys.exit("找不到 Chrome 或 Edge：安装其中一个，或把环境变量 CHROME 设成浏览器可执行文件的完整路径。")
css = Path(args.css).resolve()
if not css.is_file():
    sys.exit(f"找不到样式表：{css}")
version = re.search(r"(\d+)\.(\d+)", subprocess.run([PANDOC, "--version"], capture_output=True, text=True,
                                                     encoding="utf-8").stdout)
embed = "--embed-resources" if version and (int(version[1]), int(version[2])) >= (2, 19) else "--self-contained"

tmp = Path(tempfile.mkdtemp(prefix="md_to_pdf_"))
failed = 0
try:
    for name in args.md:
        src = Path(name).resolve()
        if not src.is_file():
            print(f"找不到 {name}")
            failed += 1
            continue
        out_dir = Path(args.out_dir).resolve() if args.out_dir else src.parent
        out_dir.mkdir(parents=True, exist_ok=True)
        pdf = out_dir / (src.stem + ".pdf")
        html = tmp / (src.stem + ".html")
        r = subprocess.run([PANDOC, str(src), "-f",
                            "markdown+hard_line_breaks+lists_without_preceding_blankline-blank_before_blockquote"
                            "-tex_math_dollars", "-t", "html5", "--standalone", embed, "--css", str(css),
                            "--resource-path", str(src.parent), "--metadata", f"pagetitle={src.stem}",
                            "-o", str(html)], capture_output=True, text=True, encoding="utf-8")
        if r.returncode:
            print(f"pandoc 转换 {src.name} 失败：{r.stderr.strip()[:300]}")
            failed += 1
            continue
        if pdf.exists():
            try:
                pdf.unlink()                    # PDF 正在阅读器里打开时删不掉，下面会报错
            except OSError:
                print(f"{pdf.name} 被占用（在阅读器里开着？），关掉再试")
                failed += 1
                continue
        subprocess.run([BROWSER, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--print-to-pdf-no-header", f"--user-data-dir={tmp / 'profile'}",
                        f"--print-to-pdf={pdf}", html.as_uri()], capture_output=True, timeout=180)
        if not pdf.is_file() or pdf.stat().st_size == 0:
            print(f"{src.name}：浏览器没有生成 PDF")
            failed += 1
            continue
        try:
            import fitz
            with fitz.open(str(pdf)) as d:
                pages = f"，{len(d)} 页"
        except Exception:
            pages = ""
        print(f"已生成：{pdf}{pages}")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
sys.exit(1 if failed else 0)
