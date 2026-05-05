# Local Library

The local library stores imported reporting material as JSONL records. It is designed for large personal archives where loading every document into memory is expensive.

## Current Stores

- `data/local_workfile_library.jsonl`: first imported local archive.
- `data/local_workfile_library_extra.jsonl`: incremental archive from additional disks and folders.
- `data/drive_land_items.jsonl`: Google Drive land data.
- `data/ifind_land_city_transactions.jsonl`: iFinD city land transaction data.

## Search

Use `search_store` for day-to-day retrieval:

```json
{
  "mode": "search_store",
  "path": "data/local_workfile_library.jsonl",
  "query": "城投 土地",
  "limit": 10
}
```

The search is streaming. It scans the JSONL file line by line and returns compact records with title, summary, source file, folder, city, company, status, and metrics.

## Summary

Use `store_summary` before working with a large data file:

```json
{
  "mode": "store_summary",
  "path": "data/local_workfile_library_extra.jsonl"
}
```

This returns record totals and counts by source, status, and file type without loading the whole store into memory.

## Import Behavior

The bulk importer handles:

- `.docx`: extracts text from the Word document body.
- `.pdf`: indexes the first pages as a preview to avoid slow full-document parsing.
- `.xlsx`, `.csv`, `.tsv`: imports rows when fields are recognized; otherwise keeps a file index record.
- `.txt`, `.html`, `.htm`: extracts plain text.

Files that are damaged, temporary Office files, or unusually slow are retained as `needs_manual_parse` records with their file path and error message.

## Practical Rule

Search first, then deep-parse the exact file needed for a story. This keeps the assistant fast while preserving access to the full archive.
