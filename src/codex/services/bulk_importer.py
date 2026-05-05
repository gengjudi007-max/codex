from __future__ import annotations

import os
import re
import signal
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set
from xml.etree import ElementTree

from codex.services.data_fetcher import extract_basic_metrics
from codex.services.document_parser import parse_document
from codex.services.evidence import source_quality
from codex.services.source_store import write_jsonl_stream
from codex.services.terminal_importer import import_terminal_file
from codex.services.text_utils import compact_text, infer_city, infer_company, normalize_text

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None


SUPPORTED_SUFFIXES: Set[str] = {
    ".csv",
    ".tsv",
    ".xlsx",
    ".txt",
    ".html",
    ".htm",
    ".pdf",
    ".docx",
}

SPREADSHEET_SUFFIXES = {".csv", ".tsv", ".xlsx"}
DOCUMENT_SUFFIXES = {".txt", ".html", ".htm"}


def import_paths(
    paths: Iterable[str],
    output_path: str,
    source: str = "local_library",
    max_files: int | None = None,
    per_file_timeout_seconds: int = 20,
    progress_every: int = 0,
) -> Dict[str, Any]:
    files = list_supported_files(paths)
    if max_files is not None:
        files = files[:max_files]

    failures: List[Dict[str, str]] = []
    counters = {"processed": 0, "items": 0}
    imported_items = _iter_imported_items(
        files,
        source=source,
        failures=failures,
        counters=counters,
        per_file_timeout_seconds=per_file_timeout_seconds,
        progress_every=progress_every,
    )
    store = write_jsonl_stream(output_path, imported_items)
    return {
        "source": source,
        "output_path": store["path"],
        "scanned_files": len(files),
        "written": store["written"],
        "total": store["total"],
        "failures": failures,
        "failure_count": len(failures),
        "suffix_counts": _suffix_counts(files),
    }


def list_supported_files(paths: Iterable[str]) -> List[Path]:
    result: List[Path] = []
    for raw_path in paths:
        path = Path(raw_path).expanduser()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            result.append(path)
            continue
        if not path.is_dir():
            continue
        for root, dirs, files in os.walk(path):
            dirs[:] = [name for name in dirs if not name.startswith(".")]
            for filename in files:
                if filename.startswith("."):
                    continue
                candidate = Path(root) / filename
                if candidate.suffix.lower() in SUPPORTED_SUFFIXES:
                    result.append(candidate)
    return sorted(result, key=lambda item: str(item))


def _with_timeout(operation, seconds: int):
    if seconds <= 0:
        return operation()

    def _raise_timeout(_signum, _frame):
        raise TimeoutError(f"单文件解析超过 {seconds} 秒")

    previous_handler = signal.signal(signal.SIGALRM, _raise_timeout)
    signal.alarm(seconds)
    try:
        return operation()
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous_handler)


def _iter_imported_items(
    files: List[Path],
    source: str,
    failures: List[Dict[str, str]],
    counters: Dict[str, int],
    per_file_timeout_seconds: int,
    progress_every: int,
):
    for index, file_path in enumerate(files, start=1):
        try:
            imported = _with_timeout(
                lambda: _import_file(file_path, source),
                per_file_timeout_seconds,
            )
        except Exception as exc:  # pragma: no cover - defensive for heterogeneous archives
            failures.append({"path": str(file_path), "error": str(exc)})
            imported = [_file_index_item(file_path, source, status="needs_manual_parse", error=str(exc))]

        for item in imported:
            counters["items"] += 1
            yield item

        counters["processed"] = index
        if progress_every and index % progress_every == 0:
            print(
                f"processed={index}/{len(files)} items={counters['items']} failures={len(failures)}",
                flush=True,
            )


def _import_file(path: Path, source: str) -> List[Dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix in SPREADSHEET_SUFFIXES:
        imported = import_terminal_file(str(path), source=source)
        if imported["items"]:
            return [_enrich_item(item, path) for item in imported["items"]]
        return [_file_index_item(path, source, status="indexed_no_rows")]
    if suffix in DOCUMENT_SUFFIXES:
        return [_enrich_item(parse_document(str(path), source=source), path)]
    if suffix == ".pdf":
        return [_text_item(path, source, _extract_pdf_preview(path), status="indexed_pdf_preview")]
    if suffix == ".docx":
        return [_docx_item(path, source)]
    return [_file_index_item(path, source, status="unsupported")]


def _docx_item(path: Path, source: str) -> Dict[str, Any]:
    text = _extract_docx_text(path)
    return _text_item(path, source, text, status="ok")


def _extract_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        if "word/document.xml" not in archive.namelist():
            return ""
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = []
    for para in root.findall(".//w:p", namespace):
        text = "".join(node.text or "" for node in para.findall(".//w:t", namespace))
        if text.strip():
            paragraphs.append(text)
    return "\n".join(paragraphs)


def _extract_pdf_preview(path: Path, max_pages: int = 3) -> str:
    if PdfReader is None:
        return path.name
    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages[:max_pages]:
        pages.append(page.extract_text() or "")
    text = "\n".join(pages).strip()
    return text or path.name


def _text_item(path: Path, source: str, text: str, status: str) -> Dict[str, Any]:
    text = re.sub(r"\s+", " ", text).strip()
    title = _title_from_text(text, path.name)
    return {
        "source": source,
        "source_file": str(path),
        "source_folder": str(path.parent),
        "file_type": path.suffix.lower().lstrip("."),
        "file_size": path.stat().st_size,
        "title": title,
        "summary": compact_text(text, 500),
        "content": text,
        "city": infer_city(text),
        "company": infer_company(text),
        "metrics": extract_basic_metrics(text),
        "source_quality": source_quality(str(path), source),
        "status": status,
    }


def _file_index_item(path: Path, source: str, status: str, error: str = "") -> Dict[str, Any]:
    return {
        "source": source,
        "source_file": str(path),
        "source_folder": str(path.parent),
        "file_type": path.suffix.lower().lstrip("."),
        "file_size": path.stat().st_size if path.exists() else 0,
        "title": path.stem,
        "summary": path.name,
        "content": path.name,
        "city": infer_city(path.name),
        "company": infer_company(path.name),
        "metrics": extract_basic_metrics(path.name),
        "source_quality": source_quality(str(path), source),
        "status": status,
        "error": error,
    }


def _enrich_item(item: Dict[str, Any], path: Path) -> Dict[str, Any]:
    enriched = dict(item)
    enriched.setdefault("source_file", str(path))
    enriched["source_folder"] = str(path.parent)
    enriched["file_type"] = path.suffix.lower().lstrip(".")
    enriched["file_size"] = path.stat().st_size
    enriched.setdefault("status", "ok")
    return enriched


def _title_from_text(text: str, fallback: str) -> str:
    for sentence in re.split(r"[。！？\n]", normalize_text(text)):
        if sentence:
            return compact_text(sentence, 80)
    return fallback


def _suffix_counts(files: Iterable[Path]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for path in files:
        key = path.suffix.lower().lstrip(".")
        counts[key] = counts.get(key, 0) + 1
    return counts
