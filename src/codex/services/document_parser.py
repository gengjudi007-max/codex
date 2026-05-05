from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from codex.services.data_fetcher import extract_basic_metrics
from codex.services.evidence import source_quality
from codex.services.text_utils import compact_text, infer_city, infer_company

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None


def parse_documents(paths: List[str], source: str = "document") -> List[Dict[str, Any]]:
    """Parse local TXT/HTML/PDF documents into standard input items."""
    return [parse_document(path, source=source) for path in paths]


def parse_document(path: str, source: str = "document") -> Dict[str, Any]:
    file_path = Path(path).expanduser()
    if not file_path.exists():
        raise FileNotFoundError(f"找不到文档：{file_path}")

    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        text = _extract_pdf_text(file_path)
    elif suffix in {".html", ".htm"}:
        text = _strip_html(file_path.read_text(encoding="utf-8", errors="ignore"))
    else:
        text = file_path.read_text(encoding="utf-8", errors="ignore")

    text = re.sub(r"\s+", " ", text).strip()
    return {
        "source": source,
        "source_file": str(file_path),
        "title": _infer_title(text, file_path.name),
        "summary": compact_text(text, 500),
        "content": text,
        "city": infer_city(text),
        "company": infer_company(text),
        "metrics": extract_basic_metrics(text),
        "source_quality": source_quality(str(file_path), source),
        "status": "ok",
    }


def _extract_pdf_text(path: Path) -> str:
    if PdfReader is None:
        raise RuntimeError("PDF 解析需要安装 pypdf。")
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _strip_html(html: str) -> str:
    html = re.sub(r"<script[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"<style[\s\S]*?</style>", " ", html, flags=re.IGNORECASE)
    html = re.sub(r"<[^>]+>", " ", html)
    return html


def _infer_title(text: str, fallback: str) -> str:
    for sentence in re.split(r"[。！？\n]", text):
        if sentence.strip():
            return compact_text(sentence.strip(), 80)
    return fallback
