from pathlib import Path
import re
import zipfile
import pandas as pd

ROOT = Path(r"D:\dongbei3sheng")
OUT = ROOT / ".codex" / "inspect_inputs_output.md"
DOCX_PATH = Path(r"D:\lin\Documents\本质上属于运筹学中的_2026-04-29-22-21-21.docx")
DOC_PATH = Path(r"D:\软件下载\xwechat_files\wxid_wdiwbl8bpcne22_0c8b\msg\file\2026-04\B题 大型展销会临时工招聘与排班优化问题_20260429175705.doc")
lines = []

def add(text=""):
    lines.append(str(text))

def compact_frame(df, rows=5):
    return df.head(rows).to_string(index=False)
def extract_docx_text(path):
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml").decode("utf-8", errors="ignore")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"</w:tr>", "\n", xml)
    xml = re.sub(r"</w:tc>", "\t", xml)
    text = re.sub(r"<[^>]+>", "", xml)
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    return re.sub(r"\n{3,}", "\n\n", text).strip()

def extract_utf16_strings(path, min_chars=4):
    data = path.read_bytes()
    raw = data.decode("utf-16le", errors="ignore")
    pattern = r"[\u4e00-\u9fffA-Za-z0-9，。；：、（）《》\-—%‰\.\s]{" + str(min_chars) + r",}"
    parts = re.findall(pattern, raw)
    cleaned = []
    for part in parts:
        part = re.sub(r"\s+", " ", part).strip()
        if len(part) >= min_chars and any("\u4e00" <= ch <= "\u9fff" for ch in part):
            cleaned.append(part)
    seen = []
    for item in cleaned:
        if item not in seen:
            seen.append(item)
    return "\n".join(seen)

add("# 输入资料检查")
add("## 文件存在性")
for p in [ROOT / "附件1.xlsx", ROOT / "附件1.xls", ROOT / "排班优化求解结果.xlsx", DOCX_PATH, DOC_PATH]:
    add(f"- {p}: exists={p.exists()}, size={p.stat().st_size if p.exists() else 'NA'}")
add("\n## 附件1.xlsx")
try:
    xf = pd.ExcelFile(ROOT / "附件1.xlsx")
    add(f"sheets={xf.sheet_names}")
    demand = pd.read_excel(ROOT / "附件1.xlsx", header=1)
    add(f"shape={demand.shape}")
    add(f"columns={list(demand.columns)}")
    add("```text")
    add(compact_frame(demand, 10))
    add("```")
    group_cols = list(demand.columns[2:12])
    add(f"小组总需求={ {str(c): int(demand[c].sum()) for c in group_cols} }")
except Exception as exc:
    add(f"附件读取失败: {type(exc).__name__}: {exc}")
add("\n## 已有结果")
try:
    out = pd.ExcelFile(ROOT / "排班优化求解结果.xlsx")
    add(f"sheets={out.sheet_names}")
    for sheet in ["Summary", "Q1_GroupTotals", "Q2_DaySummary", "Q3_DaySummary"]:
        df = pd.read_excel(ROOT / "排班优化求解结果.xlsx", sheet_name=sheet)
        add(f"\n### {sheet} shape={df.shape}")
        add("```text")
        add(df.to_string(index=False))
        add("```")
except Exception as exc:
    add(f"结果读取失败: {type(exc).__name__}: {exc}")
add("\n## 高级方法 DOCX 正文")
try:
    method_text = extract_docx_text(DOCX_PATH)
    add(method_text[:12000])
except Exception as exc:
    add(f"DOCX读取失败: {type(exc).__name__}: {exc}")

add("\n## 题目 DOC 二进制文本抽取")
try:
    problem_text = extract_utf16_strings(DOC_PATH)
    add(problem_text[:12000])
except Exception as exc:
    add(f"DOC读取失败: {type(exc).__name__}: {exc}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print(str(OUT))
