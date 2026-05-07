# Architecture

`codex` is organized as a deterministic reporting assistant for Chinese real estate financial journalism.

## Core Flow

1. Normalize raw input from free text, structured JSON, public source fetching, local documents, or terminal exports.
2. Detect reporting topics and industry signals.
3. Score topics by news value, impact, interviewability, and exclusivity.
4. Attach credibility metadata:
   - evidence
   - confidence
   - verification_status
   - limitations
   - claim_boundary
5. Generate material plans, interview plans, photography plans, and draft-edit checks.

## Trust Model

The system must not treat unmatched or single-source information as verified fact.

Output statuses:

- `verified`: original source or strong structured evidence is available.
- `needs_check`: usable as a reporting lead, but still requires cross-checking.
- `insufficient_source`: evidence is too weak for factual assertion.

## Extension Points

- Add source-specific parsers under `services/data_fetcher.py`.
- Add local-library import handling under `services/bulk_importer.py`.
- Add topic rules under `services/topic_finder.py`.
- Add metric models under dedicated service modules.
- Add tests before expanding rule coverage.

## Collection Interfaces

- `fetch_sources` accepts public URL source definitions, extracts readable text and basic metrics, and sends the collected items through topic discovery and signal monitoring. When `store_path` is provided, collected items are appended to a JSONL source store.
- `import_library` accepts local files or folders, imports supported document and spreadsheet formats, writes a deduplicated JSONL source store, and returns store statistics plus signal monitoring output.
