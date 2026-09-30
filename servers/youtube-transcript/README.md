# youtube-transcript

Pull a YouTube video's captions into your agent as clean, timestamped text — perfect for summaries, quotes, and Q&A over videos. No API key required.

Part of [mcp-minis](../../README.md), a collection of small, single-purpose MCP servers.

## Tools

| Tool | Parameters | Description |
| --- | --- | --- |
| `get_transcript` | `video` (str — URL or bare video ID), `languages` (str, default `"en"`, comma-separated preference list) | The full transcript with `[HH:MM:SS]` timestamps. |
| `list_transcripts` | `video` (str — URL or bare video ID) | All available caption tracks: language, manual vs. auto-generated, translatable or not. |

Accepted URL forms: `youtube.com/watch?v=…`, `youtu.be/…`, `/shorts/…`, `/embed/…`, `/live/…`, or a bare 11-character video ID.

> **Note:** YouTube sometimes rate-limits or blocks caption requests from datacenter IP ranges. If a fetch fails with a block/429-style error, either run the server from a residential connection or route it through a proxy by setting the `YOUTUBE_TRANSCRIPT_PROXY` environment variable (the standard `HTTPS_PROXY` also works):

```json
{
  "mcpServers": {
    "youtube-transcript": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/youtube-transcript",
        "youtube-transcript"
      ],
      "env": {
        "YOUTUBE_TRANSCRIPT_PROXY": "http://user:pass@host:port"
      }
    }
  }
}
```

## Install

From a clone of the mcp-minis repo:

```bash
cd servers/youtube-transcript
pip install .
```

Or run it in isolation with [uv](https://docs.astral.sh/uv/):

```bash
uvx --from "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/youtube-transcript" youtube-transcript
```

## Configuration

### Claude Desktop / Cursor (`claude_desktop_config.json` / `mcp.json`)

```json
{
  "mcpServers": {
    "youtube-transcript": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/youtube-transcript",
        "youtube-transcript"
      ]
    }
  }
}
```

If you installed from a local clone, use `"command": "youtube-transcript", "args": []` instead.

### Claude Code

```bash
claude mcp add youtube-transcript -- uvx --from "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/youtube-transcript" youtube-transcript
```

## Example prompts

- "Summarize this video for me: https://www.youtube.com/watch?v=dQw4w9WgXcQ"
- "What caption languages are available for video dQw4w9WgXcQ?"
- "Pull the transcript of this Short and pull out every claim it makes."

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT — see the repo [LICENSE](../../LICENSE).
