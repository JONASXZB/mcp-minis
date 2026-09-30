# arxiv-scholar

Search arXiv, read paper metadata, and export BibTeX — straight from your AI agent. No API key, no setup beyond installing the server.

Part of [mcp-minis](../../README.md), a collection of small, single-purpose MCP servers.

## Tools

| Tool | Parameters | Description |
| --- | --- | --- |
| `search_papers` | `query` (str), `max_results` (int, default 5, max 25), `sort_by` (`relevance` \| `submitted_date` \| `last_updated`) | Search arXiv. Supports field prefixes (`ti:`, `au:`, `abs:`) and boolean operators. |
| `get_paper` | `arxiv_id` (str) | Full metadata + abstract for one paper. Accepts `1706.03762`, `1706.03762v7`, or a full arXiv URL. |
| `export_bibtex` | `arxiv_ids` (list[str]) | BibTeX entries ready to paste into a `.bib` file. |

## Install

From a clone of the mcp-minis repo:

```bash
cd servers/arxiv-scholar
pip install .
```

Or run it in isolation with [uv](https://docs.astral.sh/uv/):

```bash
uvx --from "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/arxiv-scholar" arxiv-scholar
```

## Configuration

### Claude Desktop / Cursor (`claude_desktop_config.json` / `mcp.json`)

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

If you installed from a local clone, use `"command": "arxiv-scholar", "args": []` instead (make sure the environment's `bin` directory is on your `PATH`, or give the absolute path).

### Claude Code

```bash
claude mcp add arxiv-scholar -- uvx --from "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/arxiv-scholar" arxiv-scholar
```

## Example prompts

- "Search arXiv for recent papers on retrieval-augmented generation, sorted by submission date."
- "What is arXiv paper 1706.03762 about? Summarize the abstract."
- "Give me BibTeX for 1706.03762 and 2005.11401."

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT — see the repo [LICENSE](../../LICENSE).
