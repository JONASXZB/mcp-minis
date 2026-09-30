# memory-vault

Give your agent a memory that survives the session. memory-vault is a persistent local notebook — save notes today, full-text search them next week. Pure SQLite + FTS5 from the Python standard library; your data never leaves your machine, and there is no API key because there is no API.

Part of [mcp-minis](../../README.md), a collection of small, single-purpose MCP servers.

## Tools

| Tool | Parameters | Description |
| --- | --- | --- |
| `save_note` | `title` (str), `content` (str), `tags` (str, optional, comma-separated) | Save a note; returns its numeric ID. |
| `search_notes` | `query` (str) | FTS5 full-text search over title, content, and tags, best matches first. |
| `list_notes` | `tag` (str, optional) | List notes, most recently updated first, optionally filtered by tag. |
| `get_note` | `note_id` (int) | One note with its full content. |
| `delete_note` | `note_id` (int) | Permanently delete a note. |

## Where the data lives

By default the vault is a single SQLite file at `~/.memory-vault.db`. Point the server somewhere else with the `MEMORY_VAULT_DB` environment variable:

```json
{
  "mcpServers": {
    "memory-vault": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/memory-vault",
        "memory-vault"
      ],
      "env": {
        "MEMORY_VAULT_DB": "/path/to/my-vault.db"
      }
    }
  }
}
```

Back it up by copying one file. Inspect it with any SQLite browser. Delete it and the vault is gone — no cloud, no account, no lock-in.

## Install

From a clone of the mcp-minis repo:

```bash
cd servers/memory-vault
pip install .
```

Or run it in isolation with [uv](https://docs.astral.sh/uv/):

```bash
uvx --from "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/memory-vault" memory-vault
```

## Configuration

### Claude Desktop / Cursor (`claude_desktop_config.json` / `mcp.json`)

```json
{
  "mcpServers": {
    "memory-vault": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/memory-vault",
        "memory-vault"
      ]
    }
  }
}
```

If you installed from a local clone, use `"command": "memory-vault", "args": []` instead.

### Claude Code

```bash
claude mcp add memory-vault -- uvx --from "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/memory-vault" memory-vault
```

## Example prompts

- "Remember this: my preferred citation style is APA 7th. Tag it 'preferences'."
- "Search my notes for anything about the Kyoto trip."
- "What notes do I have tagged 'ielts'?"
- "Delete note #4, it's outdated."

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT — see the repo [LICENSE](../../LICENSE).
