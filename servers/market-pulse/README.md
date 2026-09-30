# market-pulse

A pocket Bloomberg terminal for your agent: stock, index, and crypto quotes plus currency conversion — all from free data sources, zero API keys.

Part of [mcp-minis](../../README.md), a collection of small, single-purpose MCP servers.

## Tools

| Tool | Parameters | Description |
| --- | --- | --- |
| `get_quote` | `symbol` (str) | Latest end-of-day quote: close, open/high/low, daily change, volume. Data: [Stooq](https://stooq.com). |
| `get_fx_rate` | `base` (str), `target` (str) | Exchange rate between two currencies (ECB reference rates). Data: [Frankfurter](https://www.frankfurter.app). |
| `convert_currency` | `amount` (float), `base` (str), `target` (str) | Convert an amount and show the rate used. |

Symbol examples: `AAPL`, `MSFT`, `^SPX` (S&P 500), `^DJI`, `BTCUSD`, `ETHUSD`, or full Stooq symbols such as `7203.JP` (Toyota).

> **Data caveats:** Stooq quotes are end-of-day, not a real-time tick feed. Frankfurter rates are ECB daily reference rates, published on business days. Great for briefings and sanity checks — not for trading.

## Install

From a clone of the mcp-minis repo:

```bash
cd servers/market-pulse
pip install .
```

Or run it in isolation with [uv](https://docs.astral.sh/uv/):

```bash
uvx --from "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/market-pulse" market-pulse
```

## Configuration

### Claude Desktop / Cursor (`claude_desktop_config.json` / `mcp.json`)

```json
{
  "mcpServers": {
    "market-pulse": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/market-pulse",
        "market-pulse"
      ]
    }
  }
}
```

If you installed from a local clone, use `"command": "market-pulse", "args": []` instead.

### Claude Code

```bash
claude mcp add market-pulse -- uvx --from "git+https://github.com/JONASXZB/mcp-minis#subdirectory=servers/market-pulse" market-pulse
```

## Example prompts

- "How did the S&P 500 close today? And how is Bitcoin doing?"
- "I'm traveling to Japan — how much is 500 USD in JPY right now?"
- "Give me a one-line market briefing: ^SPX, AAPL, BTCUSD, and USD→CNY."

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT — see the repo [LICENSE](../../LICENSE).
