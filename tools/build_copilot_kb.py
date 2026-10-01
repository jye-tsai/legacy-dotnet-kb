#!/usr/bin/env python3
"""把 HTML 知識庫轉成 Copilot agent 好讀、好 grep 的 Markdown / 純文字。

輸出到 kb/(會先清空):
  kb/*.md, kb/modules/*.md, kb/runbooks/*.md   — 各篇文件的 Markdown 版
  kb/data/screens.md                            — 畫面清冊(query.html)
  kb/data/tables.md                             — 實體表 → 使用畫面(query.html)
  kb/data/objects.md                            — SP / Function / Trigger / 報表 / 服務
  kb/data/messages.tsv                          — 錯誤訊息 → 程式位置(messages.html)
  kb/data/defects.tsv                           — 已知缺陷總表(defects.html)

只用標準函式庫。用法:python3 tools/build_copilot_kb.py
"""
import html
import json
import re
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "kb"

DOC_SOURCES = (
    sorted(ROOT.glob("*.html"))
    + sorted((ROOT / "modules").glob("*.html"))
    + sorted((ROOT / "runbooks").glob("*.html"))
)
DATA_PAGES = {"query.html", "messages.html", "defects.html"}

SKIP_TAGS = {"style", "script", "nav", "button", "head", "title", "defs", "marker"}
BLOCK_TAGS = {"p", "div", "section", "figure", "footer", "main", "header", "article"}


def esc_cell(s):
    return s.replace("|", "\\|").replace("\n", " ").strip()


class MdConverter(HTMLParser):
    """極簡 HTML → Markdown。只處理本知識庫用到的標籤。"""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []          # 最終區塊
        self.buf = []          # 目前行內文字
        self.skip = 0
        self.in_main = False
        self.pre = 0
        self.lists = []        # "ul"/"ol" 堆疊,附帶計數
        self.quote = 0
        self.table = None      # list of rows; row = list of cells
        self.cell = None
        self.cell_is_th = False
        self.svg = None        # 收集 svg 的 aria-label 與 <text>
        self.skip_div = 0          # 目前跳過中的 div.meta 層數

    # ---- helpers ----
    def flush(self):
        text = "".join(self.buf)
        self.buf = []
        if self.pre:
            return
        text = re.sub(r"[ \t\r\n]+", " ", text).strip()
        if not text:
            return
        prefix = "> " * self.quote
        self.out.append(prefix + text)

    def emit(self, s):
        self.flush()
        self.out.append(s)

    def write(self, s):
        if self.cell is not None:
            self.cell.append(s)
        else:
            self.buf.append(s)

    # ---- parser callbacks ----
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "main":
            self.in_main = True
            return
        if not self.in_main:
            return
        if tag == "svg":
            self.svg = {"label": a.get("aria-label", ""), "texts": []}
            return
        if self.svg is not None:
            return
        if tag in SKIP_TAGS or (tag == "div" and a.get("class") == "meta"):
            self.skip += 1
            if tag == "div":
                self.skip_div += 1
            return
        if self.skip:
            return
        if re.fullmatch(r"h[1-6]", tag):
            self.flush()
            self.buf.append("#" * int(tag[1]) + " ")
        elif tag in BLOCK_TAGS or tag == "blockquote":
            self.flush()
            if tag == "blockquote":
                self.quote += 1
        elif tag == "br":
            if self.cell is not None:
                self.cell.append(" ")
            else:
                self.flush()
        elif tag == "hr":
            self.emit("---")
        elif tag in ("ul", "ol"):
            self.flush()
            self.lists.append([tag, 0])
        elif tag == "li":
            self.flush()
            indent = "  " * (len(self.lists) - 1)
            if self.lists and self.lists[-1][0] == "ol":
                self.lists[-1][1] += 1
                self.buf.append(f"{indent}{self.lists[-1][1]}. ")
            else:
                self.buf.append(f"{indent}- ")
        elif tag == "pre":
            self.flush()
            self.pre += 1
            self.buf = []
        elif tag == "code" and not self.pre:
            self.write("`")
        elif tag in ("strong", "b"):
            self.write("**")
        elif tag == "table":
            self.flush()
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.table.append([])
        elif tag in ("td", "th") and self.table is not None:
            self.cell = []
            self.cell_is_th = tag == "th"
        elif tag == "figcaption":
            self.flush()
            self.buf.append("*圖:")

    def handle_endtag(self, tag):
        if tag == "main":
            self.flush()
            self.in_main = False
            return
        if not self.in_main:
            return
        if tag == "svg" and self.svg is not None:
            label, texts = self.svg["label"], self.svg["texts"]
            self.svg = None
            self.flush()
            lines = ["```text", f"[圖] {label}".rstrip()]
            if texts:
                lines.append("圖中文字:" + " / ".join(texts))
            lines.append("```")
            self.out.append("\n".join(lines))
            return
        if self.svg is not None:
            return
        if tag in SKIP_TAGS or (tag == "div" and self.skip and self.skip_div):
            if tag == "div":
                self.skip_div -= 1
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if re.fullmatch(r"h[1-6]", tag) or tag in BLOCK_TAGS or tag == "li":
            self.flush()
        elif tag == "blockquote":
            self.flush()
            self.quote = max(0, self.quote - 1)
        elif tag in ("ul", "ol"):
            self.flush()
            if self.lists:
                self.lists.pop()
        elif tag == "pre":
            code = "".join(self.buf).strip("\n")
            self.buf = []
            self.pre = max(0, self.pre - 1)
            self.out.append("```\n" + code + "\n```")
        elif tag == "code" and not self.pre:
            target = self.cell if self.cell is not None else self.buf
            if target and target[-1] == "`":
                target.pop()  # 空 code span
            else:
                target.append("`")
        elif tag in ("strong", "b"):
            self.write("**")
        elif tag in ("td", "th") and self.cell is not None:
            text = re.sub(r"\s+", " ", "".join(self.cell)).strip()
            if self.table:
                self.table[-1].append((text, self.cell_is_th))
            self.cell = None
        elif tag == "table" and self.table is not None:
            self.out.append(self.render_table(self.table))
            self.table = None
        elif tag == "figcaption":
            self.buf.append("*")
            self.flush()

    def handle_data(self, data):
        if not self.in_main:
            return
        if self.svg is not None:
            t = data.strip()
            if t:
                self.svg["texts"].append(t)
            return
        if self.skip:
            return
        self.write(data)

    @staticmethod
    def render_table(rows):
        rows = [r for r in rows if r]
        if not rows:
            return ""
        width = max(len(r) for r in rows)
        norm = [[esc_cell(c[0]) for c in r] + [""] * (width - len(r)) for r in rows]
        if all(c[1] for c in rows[0]):
            head, body = norm[0], norm[1:]
        else:
            head, body = [""] * width, norm
        lines = ["| " + " | ".join(head) + " |", "|" + "---|" * width]
        lines += ["| " + " | ".join(r) + " |" for r in body]
        return "\n".join(lines)

    def result(self):
        self.flush()
        text = "\n\n".join(b for b in self.out if b.strip())
        return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def link_fix(md):
    # 文件內互相引用的 .html 改指 .md
    return re.sub(r"(\b[\w\-]+)\.html\b", r"\1.md", md)


def convert_doc(src):
    rel = src.relative_to(ROOT)
    raw = src.read_text(encoding="utf-8")
    m = re.search(r"<title>(.*?)</title>", raw, re.S)
    title = html.unescape(m.group(1)).strip() if m else rel.stem
    date = re.search(r'name="doc-date" content="([^"]+)"', raw)
    p = MdConverter()
    p.feed(raw)
    body = link_fix(p.result())
    head = f"<!-- 由 tools/build_copilot_kb.py 從 {rel.as_posix()} 產生,請勿手改 -->\n"
    if date:
        head += f"<!-- doc-date: {date.group(1)} -->\n"
    if not body.lstrip().startswith("# "):
        head += f"\n# {title}\n"
    dst = OUT / rel.with_suffix(".md")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(head + "\n" + body, encoding="utf-8")
    return dst


def load_json(name):
    raw = (ROOT / name).read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="data">(.*?)</script>', raw, re.S)
    return json.loads(m.group(1))


def tsv(v):
    if isinstance(v, (list, tuple)):
        v = ", ".join(str(x) for x in v)
    return str(v if v is not None else "").replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def build_query_data():
    d = load_json("query.html")
    dirs, files = d["D"], d["P"]

    def path(i):
        if not isinstance(i, int) or i < 0 or i >= len(files):
            return ""
        di, fn = files[i]
        return f"{dirs[di]}/{fn}"

    layer_names = ["ui", "pxy", "ctl", "po", "model", "view"]
    lines = [
        "# 畫面清冊(911 支)",
        "",
        "由 query.html 內嵌資料產生。欄位:代號 | 模組 | 型別(M 維護/Q 查詢/R 報表/B 批次…) | 名稱 | 主檔表 | 明細表 | PO 基底 | 各層檔案",
        "",
        "| 代號 | 模組 | 型別 | 名稱 | 主檔表 | 明細表 | PO 基底 | 各層檔案 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for s in d["S"]:
        L = s.get("L") or {}
        layers = "; ".join(f"{k}={path(L[k])}" for k in layer_names if k in L)
        lines.append("| " + " | ".join(esc_cell(tsv(x)) for x in [
            s.get("c"), s.get("m"), s.get("k"), s.get("n"), s.get("mt"),
            s.get("dt"), s.get("pb"), layers]) + " |")
    (OUT / "data" / "screens.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    lines = [
        "# 實體表(437 張)→ 使用畫面",
        "",
        "由 query.html 內嵌資料產生。主檔於 = 以此表為主檔的畫面;明細於 = 以此表為明細的畫面;EVA = 是否走四眼覆核;引用數 = SQL 中 FROM / JOIN 次數。",
        "",
        "| 表 | 主檔於 | 明細於 | 模組 | EVA | 引用數 | 欄位 |",
        "|---|---|---|---|---|---|---|",
    ]
    for t in d["T"]:
        rc = t.get("rc") or {}
        refs = ", ".join(f"{k}:{v}" for k, v in rc.items())
        cols = t.get("cols") or []
        cols = [c if isinstance(c, str) else (c[0] if c else "") for c in cols]
        lines.append("| " + " | ".join(esc_cell(tsv(x)) for x in [
            t.get("t"), t.get("mo"), t.get("do"), t.get("mods"),
            t.get("eva"), refs, cols]) + " |")
    (OUT / "data" / "tables.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    lines = ["# 資料庫物件 / 報表範本 / 服務", "", "由 query.html 內嵌資料產生。", "",
             "## SP / Function / Trigger", "", "| 名稱 | 種類 | 檔案 | 使用畫面 |", "|---|---|---|---|"]
    for o in d["O"]:
        lines.append("| " + " | ".join(esc_cell(tsv(x)) for x in [
            o.get("n"), o.get("k"), path(o.get("f")), o.get("u")]) + " |")
    lines += ["", "## 報表範本", "", "| 名稱 | 檔案 | 使用畫面 |", "|---|---|---|"]
    for r in d["R"]:
        lines.append("| " + " | ".join(esc_cell(tsv(x)) for x in [
            r.get("n"), path(r.get("f")), r.get("s")]) + " |")
    lines += ["", "## Windows 服務", "", "| 名稱 | 檔案 |", "|---|---|"]
    for v in d["V"]:
        lines.append(f"| {esc_cell(tsv(v.get('n')))} | {esc_cell(path(v.get('f')))} |")
    (OUT / "data" / "objects.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_messages():
    d = load_json("messages.html")
    lines = ["訊息\t呼叫方式\t檔案:行號"]
    for r in d["rows"]:
        lines.append("\t".join([tsv(r.get("t")), tsv(r.get("c")), f"{tsv(r.get('f'))}:{tsv(r.get('n'))}"]))
    (OUT / "data" / "messages.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_defects():
    d = load_json("defects.html")
    lines = ["模組\t嚴重度\t缺陷型別與描述\t涉及畫面\t位置/範圍\t程式錨點"]
    for r in d["rows"]:
        lines.append("\t".join(tsv(r.get(k)) for k in ("m", "s", "e", "c", "u", "a")))
    (OUT / "data" / "defects.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "data").mkdir(parents=True)
    n = 0
    for src in DOC_SOURCES:
        if src.name in DATA_PAGES and src.parent == ROOT:
            continue
        convert_doc(src)
        n += 1
    build_query_data()
    build_messages()
    build_defects()
    total = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file())
    print(f"converted {n} docs + 5 data files -> {OUT.relative_to(ROOT)}/ ({total/1e6:.1f} MB)", file=sys.stderr)


if __name__ == "__main__":
    main()
