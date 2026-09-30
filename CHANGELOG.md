# Changelog

All notable changes to mcp-minis are documented here.

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
