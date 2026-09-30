# mcp-minis

**Five tiny, single-purpose [MCP](https://modelcontextprotocol.io) servers that give your AI agent superpowers — no API keys, no sign-ups, no bloat.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![MCP](https://img.shields.io/badge/Protocol-MCP-6E56CF)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

## Why mcp-minis?

Most MCP servers try to do everything. These do one thing each — and do it well:

- **Small** — every server is a single readable Python file you can audit in minutes.
- **Single-purpose** — search papers *or* fetch a transcript *or* check a quote. Nothing else.
- **No API keys** — every data source is free and keyless (arXiv, YouTube captions, Stooq, Frankfurter, your own disk).
- **Works anywhere** — standard MCP over stdio: Claude Code, Claude Desktop, Cursor, or any other MCP client.
- **Honest failure** — tools return clear error strings instead of crashing your session.

## The servers

| Server | What it does | Data source |
| --- | --- | --- |
| [arxiv-scholar](servers/arxiv-scholar/) | Search arXiv, read paper metadata, export BibTeX | arXiv API |
| [youtube-transcript](servers/youtube-transcript/) | Fetch YouTube captions as timestamped text | YouTube captions |
| [web-to-markdown](servers/web-to-markdown/) | Turn any web page into clean, readable Markdown | trafilatura extraction |
| [market-pulse](servers/market-pulse/) | Stock / index / crypto quotes and currency conversion | Stooq + Frankfurter |
| [memory-vault](servers/memory-vault/) | A persistent, full-text-searchable notebook for your agent | Local SQLite (FTS5) |

Each server's README lists its tools, parameters, and copy-paste configs.

## Quick Start

### Option A — run any server straight from GitHub (no clone)

With [uv](https://docs.astral.sh/uv/) installed, point your MCP client at a server package:

```json
{
  "mcpServers": {
    "arxiv-scholar": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/arxiv-scholar",
        "arxiv-scholar"
      ]
    }
  }
}
```

Swap `arxiv-scholar` for any other server name (in both places) to use a different mini.

For Claude Code, the equivalent is one command:

```bash
claude mcp add arxiv-scholar -- uvx --from "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/arxiv-scholar" arxiv-scholar
```

### Option B — clone and install

```bash
git clone https://github.com/JONASXZB/mcp-minis.git
cd mcp-minis/servers/arxiv-scholar
pip install .
```

Then register the command with your client:

```json
{
  "mcpServers": {
    "arxiv-scholar": { "command": "arxiv-scholar", "args": [] }
  }
}
```

### Want all five at once?

Grab a ready-made combined config from [`examples/`](examples/):

- [`examples/claude_desktop_config.json`](examples/claude_desktop_config.json) — Claude Desktop / Cursor
- [`examples/mcp.json`](examples/mcp.json) — generic MCP client config

## Roadmap

- [ ] `weather-now` — current conditions + forecast from Open-Meteo (also keyless)
- [ ] `rss-reader` — fetch and summarize RSS/Atom feeds
- [ ] `pdf-reader` — extract text and structure from PDF files
- [ ] PyPI releases for each mini, so `uvx arxiv-scholar` just works
- [ ] Streamable HTTP transport option for hosted use

Ideas for a mini you'd actually use? [Open an issue](https://github.com/JONASXZB/mcp-minis/issues) — or better, [add one yourself](CONTRIBUTING.md).

## Contributing

PRs are welcome — especially new minis that follow the house rules: one job, free data, no API keys, minimal dependencies, graceful errors. See [CONTRIBUTING.md](CONTRIBUTING.md) for the template conventions every server follows.

## License

MIT — see [LICENSE](LICENSE). Use these however you like.
