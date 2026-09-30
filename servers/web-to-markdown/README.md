# web-to-markdown

Give your agent eyes for the web: hand it a URL, get back the page's main content as clean Markdown — navigation, ads, and boilerplate stripped out. No API key required.

Part of [mcp-minis](../../README.md), a collection of small, single-purpose MCP servers.

## Tools

| Tool | Parameters | Description |
| --- | --- | --- |
| `fetch_markdown` | `url` (str), `max_chars` (int, default 20000) | Fetch a page and return its main content as Markdown (links and tables preserved), prefixed with the page title. |
| `fetch_title_and_summary` | `url` (str) | Just the title, author/date when available, and a short summary — ideal for triaging a pile of links. |

Content extraction is done by [trafilatura](https://github.com/adbar/trafilatura); fetching uses `httpx` with a normal browser User-Agent.

## Install

From a clone of the mcp-minis repo:

```bash
cd servers/web-to-markdown
pip install .
```

Or run it in isolation with [uv](https://docs.astral.sh/uv/):

```bash
uvx --from "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/web-to-markdown" web-to-markdown
```

## Configuration

### Claude Desktop / Cursor (`claude_desktop_config.json` / `mcp.json`)

```json
{
  "mcpServers": {
    "web-to-markdown": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/web-to-markdown",
        "web-to-markdown"
      ]
    }
  }
}
```

If you installed from a local clone, use `"command": "web-to-markdown", "args": []` instead.

### Claude Code

```bash
claude mcp add web-to-markdown -- uvx --from "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/web-to-markdown" web-to-markdown
```

## Example prompts

- "Read this article and give me the three key arguments: https://example.com/some-article"
- "Here are five links — fetch just the title and summary of each so I can decide what to read."
- "Fetch this docs page as Markdown and save the important parts to my notes."

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT — see the repo [LICENSE](../../LICENSE).
