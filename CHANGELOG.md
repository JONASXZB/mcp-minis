# Changelog

All notable changes to mcp-minis are documented here.

## [0.6.0] — 2026-10-01

### Fixed
- **arxiv-scholar**: `get_paper` and `export_bibtex` no longer break old-style arXiv IDs (the pre-2007 `hep-th/9901001` format). A shared `_normalize_arxiv_id` helper now understands bare new-style and old-style IDs, `arxiv:` prefixes, version suffixes, and abs/pdf URLs — previously an old-style URL was truncated to `9901001` and the paper was never found. `export_bibtex` also strips version suffixes with a regex instead of `split("v")` when checking for missing IDs.
- **web-to-markdown**: URLs that serve a non-HTML file (PDF, images, archives, …) are now rejected with an error naming the actual content type, instead of being decoded as garbled text and reported as "no readable content". HTML/XML pages are unaffected; responses with no declared content type are still processed as before.

### Changed
- arxiv-scholar and web-to-markdown bumped to 0.3.0; youtube-transcript remains at 0.3.0, memory-vault at 0.4.0, market-pulse at 0.3.0.
- Synced the stale `__version__` strings in all five `__init__.py` files to match their pyproject versions (they were left at 0.1.0/0.2.0 by earlier releases).

## [0.5.0] — 2026-10-01

### Added
- **youtube-transcript**: `get_transcript` now takes `start_line` and `max_lines` parameters, so a long video's captions can be paged through instead of flooding the calling agent's context in a single call. When paging, the header reports the shown range and the total line count; the default (no paging arguments) still returns the full transcript.

### Fixed
- **youtube-transcript**: when YouTube blocks transcript requests from the current IP (`RequestBlocked` / `IpBlocked`), the error now says so explicitly and points at the `YOUTUBE_TRANSCRIPT_PROXY` workaround, instead of surfacing the library's raw exception text.

### Changed
- youtube-transcript bumped to 0.3.0; memory-vault remains at 0.4.0, market-pulse at 0.3.0, arxiv-scholar and web-to-markdown at 0.2.0.

## [0.4.0] — 2026-10-01

### Changed
- **memory-vault**: `search_notes` and `list_notes` now take a `limit` parameter (default 20, max 100) and always report the total number of matches, so a large vault can no longer flood the calling agent's context with unbounded results — and a truncated list is never mistaken for the whole vault.

### Fixed
- **arxiv-scholar**: `export_bibtex` now escapes LaTeX special characters (`&`, `%`, `_`, `#`, `$`, braces, `~`, `^`, `\`) in titles and author names, so papers whose titles contain them no longer produce broken `.bib` entries. URLs and arXiv IDs are left untouched.
- **web-to-markdown**: page downloads are now streamed with a 10 MB size cap instead of being loaded into memory whole; oversized pages return a clear error.

### Changed
- memory-vault bumped to 0.4.0; arxiv-scholar and web-to-markdown bumped to 0.2.0; youtube-transcript remains at 0.2.0, market-pulse at 0.3.0.

## [0.3.0] — 2026-10-01

### Fixed
- **memory-vault**: `update_note` no longer treats an empty string as "leave unchanged", which made it impossible to clear a note's tags or empty its body. Fields are now `Optional`: omit a field to keep its current value, pass `tags=""` to clear all tags, or `content=""` to empty the body. (A title still cannot be cleared — a passed title must be non-empty.)
- **market-pulse**: `convert_currency` now short-circuits instead of calling the Frankfurter API when converting a currency into itself (rate 1.0000) or converting an amount of 0 — mirroring the same-currency shortcut `get_fx_rate` already had.

### Changed
- memory-vault and market-pulse bumped to 0.3.0; arxiv-scholar and web-to-markdown remain at 0.1.0, youtube-transcript at 0.2.0.

## [0.2.0] — 2026-10-01

### Added
- **memory-vault**: new `update_note` tool — edit a note's title, content, or tags in place (the FTS index follows automatically). The server now exposes 6 tools.
- **youtube-transcript**: proxy support. Set `YOUTUBE_TRANSCRIPT_PROXY` (or the standard `HTTPS_PROXY`) to route caption requests through a proxy — the standard workaround when YouTube blocks datacenter IPs.
- Continuous integration: GitHub Actions runs every server's test suite on Python 3.10 and 3.12.

### Changed
- **market-pulse**: quote requests now send a browser User-Agent header, which reduces false rejections from Stooq's free CSV feed.
- memory-vault, youtube-transcript, and market-pulse bumped to 0.2.0; arxiv-scholar and web-to-markdown remain at 0.1.0.

## [0.1.0] — 2026-10-01

Initial release: five single-purpose MCP servers — arxiv-scholar, youtube-transcript, web-to-markdown, market-pulse, memory-vault — 16 tools total, no API keys, MIT license.
