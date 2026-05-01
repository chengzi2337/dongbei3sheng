from __future__ import annotations

import json
import sys
from pathlib import Path

from pypdf import PdfReader


def extract_pdf(pdf_path: Path, output_dir: Path) -> None:
    reader = PdfReader(str(pdf_path))
    pages = []
    for index, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append({"page": index + 1, "chars": len(text), "text": text})

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = pdf_path.stem
    full_text = "\n\n".join(f"## 第 {item['page']} 页\n\n{item['text']}" for item in pages)
    (output_dir / f"{stem}.md").write_text(full_text, encoding="utf-8")

    preview_pages = pages[:12] + pages[-8:] if len(pages) > 20 else pages
    preview = "\n\n".join(f"## 第 {item['page']} 页\n\n{item['text']}" for item in preview_pages)
    (output_dir / f"{stem}-preview.md").write_text(preview, encoding="utf-8")

    summary = {
        "path": str(pdf_path),
        "pages": len(pages),
        "chars": sum(item["chars"] for item in pages),
        "empty_pages": [item["page"] for item in pages if item["chars"] == 0],
        "preview": str(output_dir / f"{stem}-preview.md"),
        "full": str(output_dir / f"{stem}.md"),
    }
    (output_dir / f"{stem}-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("用法：extract_pdf_text.py <pdf> <output_dir>")
    extract_pdf(Path(sys.argv[1]), Path(sys.argv[2]))


if __name__ == "__main__":
    main()
