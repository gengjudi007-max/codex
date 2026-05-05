# Architecture

`codex` is organized as a deterministic reporting assistant for Chinese real estate financial journalism.

## Core Flow

1. Normalize raw input from free text, structured JSON, or public source fetching.
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
- Add topic rules under `services/topic_finder.py`.
- Add metric models under dedicated service modules.
- Add tests before expanding rule coverage.
