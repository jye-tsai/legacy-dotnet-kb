#!/usr/bin/env python3
"""把 kb/ 打包成 Microsoft 365 Copilot Agent Builder 可上傳的知識檔。

Agent Builder 限制:「知識」每個 agent 最多 20 個檔、不收 .md,所以合併成 .txt。
輸出到 m365/(會先清空;不產 zip,有些公司網路擋 zip 下載):
  m365/knowledge/   — 「知識」上傳用(16 個 .txt)
  m365/SKILL.txt    — SKILL.md 的 .txt 版(擋 .md 下載時用,下載後改名回 SKILL.md)
  m365/skill/       — 「技能」用:SKILL.md + references/ 16 個 .md;
                      使用者自己把 SKILL.md 與 references/ 一起壓成 zip(SKILL.md 要在 zip 根目錄)
技能的 SKILL.md 來源是 tools/m365_skill/SKILL.md。
先跑 tools/build_copilot_kb.py 產生 kb/,再跑本腳本。
"""
import csv
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "kb"
OUT = ROOT / "m365"
KNOW = OUT / "knowledge"

# 輸出檔名 → (說明, 來源 md 清單)
BUNDLES = {
    "01-導覽-索引速查症狀.txt": ("入口、讀序、速查卡、症狀路由表、模組與手冊索引",
        ["index.md", "CHEATSHEET.md", "TROUBLESHOOT.md", "modules/README.md", "runbooks/README.md"]),
    "02-系統介紹-業務軸.txt": ("六條業務線、一日作業時序、端到端流程", ["OVERVIEW.md"]),
    "03-技術架構.txt": ("六層架構、Remoting、四眼 EVA 引擎、資料庫", ["architecture.md"]),
    "04-維護手冊-runbooks.txt": ("加欄位、加畫面、加查詢、加批次、加報表、改四眼、改 SP、部署、建環境",
        ["runbooks/add-column.md", "runbooks/add-screen.md", "runbooks/add-query-screen.md",
         "runbooks/add-batch.md", "runbooks/add-report.md", "runbooks/change-eva-flow.md",
         "runbooks/change-sp-fn-trigger.md", "runbooks/deploy.md", "runbooks/build-env.md"]),
    "10-模組-BBS-BMS-CAS-CLS-COD.txt": ("", ["modules/bbs.md", "modules/bms.md", "modules/cas.md", "modules/cls.md", "modules/cod.md"]),
    "11-模組-CPM-CRM-DSM-TMK.txt": ("", ["modules/cpm.md", "modules/crm.md", "modules/dsm.md", "modules/tmk.md"]),
    "12-模組-EC-MISC-RSP-NFDR.txt": ("", ["modules/ec.md", "modules/misc.md", "modules/rsp.md", "modules/nfdr1.md", "modules/nfdr2.md"]),
    "13-模組-OFD1至5.txt": ("", ["modules/ofd123.md", "modules/ofd4.md", "modules/ofd5.md"]),
    "14-模組-OFD6至9.txt": ("", ["modules/ofd6.md", "modules/ofd7.md", "modules/ofd8.md", "modules/ofd9.md"]),
    "15-模組-OFDB批次.txt": ("", ["modules/ofdb.md", "modules/ofdb3.md", "modules/ofdb4.md", "modules/ofdb5.md"]),
    "16-模組-OFDI查詢-OFDR報表.txt": ("", ["modules/ofdi1.md", "modules/ofdi2.md", "modules/ofdr1.md", "modules/ofdr2.md"]),
}


def strip_md_comments(text):
    return re.sub(r"<!--.*?-->\n?", "", text, flags=re.S).strip()


def build_bundles():
    for name, (desc, sources) in BUNDLES.items():
        parts = [f"ATLAS 知識庫 — {name[:-4]}", desc, "本檔合併以下文件:" + "、".join(sources), ""]
        for src in sources:
            body = strip_md_comments((KB / src).read_text(encoding="utf-8"))
            parts += ["", "=" * 60, f"【文件】kb/{src}", "=" * 60, "", body]
        (KNOW / name).write_text("\n".join(parts) + "\n", encoding="utf-8")


def md_tables(path):
    """讀 kb/data/*.md 所有表 → [(小節標題, 表頭, 列)]。"""
    out, title, header, rows = [], "", None, []
    for line in path.read_text(encoding="utf-8").splitlines() + [""]:
        if line.startswith("#"):
            title = line.lstrip("# ").strip()
        if line.startswith("|"):
            cells = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
            if set("".join(cells)) <= set("-"):
                continue
            if header is None:
                header = cells
            else:
                rows.append(cells)
        elif header is not None:
            out.append((title, header, rows))
            header, rows = None, []
    return out


def records(title, intro, groups, key_label):
    """一筆一行的「欄位:值」格式,語意搜尋切塊時每行自成一筆。"""
    lines = [title, intro, ""]
    for sub, header, rows in groups:
        if sub:
            lines += ["", f"## {sub}", ""]
        for r in rows:
            pairs = [f"{h}:{v}" for h, v in zip(header, r) if v]
            lines.append(f"[{key_label} {r[0]}] " + " | ".join(pairs))
    return "\n".join(lines) + "\n"


def tsv_groups(path):
    with path.open(encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE))
    return [("", rows[0], rows[1:])]


def build_data():
    d = KB / "data"
    (KNOW / "20-資料-畫面清冊.txt").write_text(records(
        "ATLAS 畫面清冊(911 支)",
        "每行一支畫面。型別:M 維護 / I 查詢 / B 批次 / R 報表。各層檔案:ui / pxy(FormProxy)/ ctl(Control)/ po / model / view。",
        md_tables(d / "screens.md"), "畫面"), encoding="utf-8")
    (KNOW / "21-資料-實體表.txt").write_text(records(
        "ATLAS 實體表(437 張)→ 使用畫面",
        "每行一張表。主檔於 = 以此表為主檔的畫面;明細於 = 以此表為明細的畫面;EVA = 是否走四眼覆核。",
        md_tables(d / "tables.md"), "表"), encoding="utf-8")
    (KNOW / "22-資料-SP報表服務.txt").write_text(records(
        "ATLAS 資料庫物件(SP / Function / Trigger)、報表範本、Windows 服務",
        "每行一個物件。",
        md_tables(d / "objects.md"), "物件"), encoding="utf-8")
    (KNOW / "23-資料-錯誤訊息反查.txt").write_text(records(
        "ATLAS 錯誤訊息反查(9,440 條)",
        "每行一條訊息原文與丟出位置(檔案:行號)。使用者回報錯誤時,用訊息片段搜尋本檔。{…} 代表程式組字串的變數部分。",
        tsv_groups(d / "messages.tsv"), "訊息"), encoding="utf-8")
    (KNOW / "24-資料-已知缺陷.txt").write_text(records(
        "ATLAS 已知缺陷總表(1,682 條)",
        "每行一條缺陷:模組、嚴重度、缺陷型別與描述、涉及畫面、位置、程式錨點。",
        tsv_groups(d / "defects.tsv"), "缺陷"), encoding="utf-8")


SKILL_SRC = Path(__file__).resolve().parent / "m365_skill" / "SKILL.md"
SKILL = OUT / "skill"
# references/ 檔名(英文,避免 Windows 壓縮亂碼)→ knowledge/ 裡的來源
SKILL_REFS = {
    "01-guide.md": "01-導覽-索引速查症狀.txt",
    "02-overview.md": "02-系統介紹-業務軸.txt",
    "03-architecture.md": "03-技術架構.txt",
    "04-runbooks.md": "04-維護手冊-runbooks.txt",
    "10-modules-bbs-bms-cas-cls-cod.md": "10-模組-BBS-BMS-CAS-CLS-COD.txt",
    "11-modules-cpm-crm-dsm-tmk.md": "11-模組-CPM-CRM-DSM-TMK.txt",
    "12-modules-ec-misc-rsp-nfdr.md": "12-模組-EC-MISC-RSP-NFDR.txt",
    "13-modules-ofd1-5.md": "13-模組-OFD1至5.txt",
    "14-modules-ofd6-9.md": "14-模組-OFD6至9.txt",
    "15-modules-ofdb.md": "15-模組-OFDB批次.txt",
    "16-modules-ofdi-ofdr.md": "16-模組-OFDI查詢-OFDR報表.txt",
    "20-screens.md": "20-資料-畫面清冊.txt",
    "21-tables.md": "21-資料-實體表.txt",
    "22-objects.md": "22-資料-SP報表服務.txt",
    "23-messages.md": "23-資料-錯誤訊息反查.txt",
    "24-defects.md": "24-資料-已知缺陷.txt",
}


def build_skill():
    """技能資料夾:SKILL.md + references/ 16 個 .md(內容同知識檔)。"""
    refs = SKILL / "references"
    refs.mkdir(parents=True)
    shutil.copyfile(SKILL_SRC, SKILL / "SKILL.md")
    # 同內容的 .txt:有些公司網路擋 .md 下載,下載後改名回 SKILL.md 再壓 zip
    shutil.copyfile(SKILL_SRC, OUT / "SKILL.txt")
    for dst, src in SKILL_REFS.items():
        shutil.copyfile(KNOW / src, refs / dst)
    skill_md = SKILL_SRC.read_text(encoding="utf-8")
    assert len(skill_md) < 20000, "SKILL.md 指示上限 20,000 字"
    for name in SKILL_REFS:
        assert f"references/{name}" in skill_md, f"SKILL.md 沒提到 references/{name}"
    total = sum(f.stat().st_size for f in SKILL.rglob("*") if f.is_file())
    assert total < 50e6, "技能套件上限 50 MB"
    return total


def main():
    if not KB.exists():
        sys.exit("找不到 kb/,請先跑 python3 tools/build_copilot_kb.py")
    keep = {p.name: p.read_bytes() for p in OUT.glob("*.txt")} if OUT.exists() else {}
    if OUT.exists():
        shutil.rmtree(OUT)
    KNOW.mkdir(parents=True)
    for name, data in keep.items():  # 說明文字等手寫檔保留
        (OUT / name).write_bytes(data)
    build_bundles()
    build_data()
    files = sorted(KNOW.iterdir())
    assert len(files) <= 20, f"Agent Builder 最多 20 個檔,目前 {len(files)}"
    skill_bytes = build_skill()
    for f in files:
        print(f"{f.stat().st_size/1e6:6.2f} MB  {f.name}", file=sys.stderr)
    print(f"skill: {SKILL.relative_to(ROOT)}/ ({skill_bytes/1e6:.1f} MB, {len(SKILL_REFS) + 1} files)", file=sys.stderr)
    print(f"{len(files)} files -> {KNOW.relative_to(ROOT)}/", file=sys.stderr)


if __name__ == "__main__":
    main()
