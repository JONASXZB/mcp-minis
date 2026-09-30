# Changelog

All notable changes to mcp-minis are documented here.

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

Initial release: five single-purpose MCP servers — arxiv-scholar, youtube-transcript, web-to-markdown, market-pulse, memory-vault — 15 tools total, no API keys, MIT license.
