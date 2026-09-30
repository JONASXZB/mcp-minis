"""market-pulse MCP server.

Quick market data for agents: end-of-day stock / index / crypto quotes from
Stooq's free CSV feed, and currency conversion from the Frankfurter API
(European Central Bank reference rates). No API keys anywhere.

Note: Stooq quotes are end-of-day (not real-time tick data), and Frankfurter
rates are daily reference rates published on business days.

Run with: ``market-pulse`` (stdio transport).
"""

from __future__ import annotations

import csv
import io

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("market-pulse")

_STOOQ_URL = "https://stooq.com/q/l/"
_FRANKFURTER_URL = "https://api.frankfurter.dev/v1/latest"
_TIMEOUT_SECONDS = 20.0
# Stooq's free CSV feed sometimes gates non-browser clients; a normal
# browser User-Agent noticeably reduces false rejections.
_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    )
}


def _stooq_symbol(symbol: str) -> str:
    """Normalize a user symbol to Stooq's convention.

    - Indices keep their caret: ``^SPX`` -> ``^spx``
    - Crypto pairs are bare lowercase: ``BTCUSD`` -> ``btcusd``
    - Symbols that already contain a dot (``AAPL.US``, ``7203.JP``) pass through
    - Everything else is treated as a US-listed stock: ``AAPL`` -> ``aapl.us``
    """
    cleaned = symbol.strip().lower()
    if cleaned.startswith("^"):
        return cleaned
    if "." in cleaned:
        return cleaned
    if cleaned.endswith("usd") and len(cleaned) > 3:
        return cleaned
    return f"{cleaned}.us"


@mcp.tool()
def get_quote(symbol: str) -> str:
    """Get the latest (end-of-day) quote for a stock, index, or crypto pair.

    Data source: Stooq. Examples of accepted symbols:
    ``AAPL`` (Apple), ``MSFT``, ``^SPX`` (S&P 500), ``^DJI`` (Dow Jones),
    ``BTCUSD`` (Bitcoin), ``ETHUSD``, or explicit Stooq symbols like
    ``7203.JP`` (Toyota).

    Args:
        symbol: The ticker symbol, case-insensitive.

    Returns:
        Open/high/low/close, daily change, and volume — or an error message
        if the symbol is unknown or the feed is unreachable.
    """
    if not symbol.strip():
        return "Error: symbol must not be empty."
    stooq_symbol = _stooq_symbol(symbol)
    params = {"s": stooq_symbol, "f": "sd2t2ohlcv", "h": "", "e": "csv"}
    try:
        with httpx.Client(
            timeout=_TIMEOUT_SECONDS, follow_redirects=True, headers=_BROWSER_HEADERS
        ) as client:
            response = client.get(_STOOQ_URL, params=params)
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return (
            f"Error: Stooq returned HTTP {exc.response.status_code} for '{symbol}'. "
            "Stooq sometimes gates its free CSV feed behind a browser check; "
            "try again later or from a different network."
        )
    except (httpx.HTTPError, httpx.InvalidURL) as exc:
        return f"Error: failed to fetch quote for '{symbol}': {exc}"
    rows = list(csv.DictReader(io.StringIO(response.text)))
    if not rows or rows[0].get("Close") in (None, "", "N/D"):
        return (
            f"Error: no quote data for '{symbol}' (Stooq symbol '{stooq_symbol}'). "
            "Check the symbol spelling."
        )
    row = rows[0]
    try:
        open_ = float(row["Open"])
        close = float(row["Close"])
        high = float(row["High"])
        low = float(row["Low"])
    except (KeyError, TypeError, ValueError):
        return f"Error: could not parse quote data for '{symbol}': {row}"
    change = close - open_
    change_pct = (change / open_ * 100) if open_ else 0.0
    sign = "+" if change >= 0 else ""
    lines = [
        f"{symbol.strip().upper()} (Stooq: {stooq_symbol})",
        f"Date: {row.get('Date', 'n/a')} {row.get('Time', '')}".rstrip(),
        f"Close: {close:,.2f}",
        f"Open: {open_:,.2f}  High: {high:,.2f}  Low: {low:,.2f}",
        f"Change (vs open): {sign}{change:,.2f} ({sign}{change_pct:.2f}%)",
    ]
    volume = row.get("Volume")
    if volume and volume != "N/D":
        lines.append(f"Volume: {int(float(volume)):,}")
    lines.append("Note: end-of-day data from Stooq, not a real-time feed.")
    return "\n".join(lines)


def _fetch_fx(amount: float, base: str, target: str) -> dict:
    """Call the Frankfurter API and return the parsed JSON payload."""
    params = {"amount": amount, "from": base.upper(), "to": target.upper()}
    with httpx.Client(timeout=_TIMEOUT_SECONDS, follow_redirects=True) as client:
        response = client.get(_FRANKFURTER_URL, params=params)
        response.raise_for_status()
        return response.json()


@mcp.tool()
def get_fx_rate(base: str, target: str) -> str:
    """Get the exchange rate between two currencies.

    Rates are ECB daily reference rates via the Frankfurter API.

    Args:
        base: Base currency code, e.g. ``USD``.
        target: Target currency code, e.g. ``CNY`` or ``EUR``.

    Returns:
        The rate (1 unit of base = X units of target) and its reference
        date — or an error message for unknown currency codes.
    """
    base, target = base.strip().upper(), target.strip().upper()
    if len(base) != 3 or len(target) != 3:
        return "Error: currency codes must be 3 letters, e.g. USD, EUR, CNY."
    if base == target:
        return f"1 {base} = 1.0000 {target} (same currency)"
    try:
        data = _fetch_fx(1.0, base, target)
        rate = data["rates"][target]
    except httpx.HTTPStatusError as exc:
        return (
            f"Error: Frankfurter API returned HTTP {exc.response.status_code}. "
            f"'{base}' or '{target}' may not be a supported currency code."
        )
    except (httpx.HTTPError, httpx.InvalidURL, KeyError, TypeError, ValueError) as exc:
        return f"Error: failed to fetch FX rate {base}->{target}: {exc}"
    return (
        f"1 {base} = {rate:.4f} {target}\n"
        f"Reference date: {data.get('date', 'n/a')} (ECB daily reference rate via Frankfurter)"
    )


@mcp.tool()
def convert_currency(amount: float, base: str, target: str) -> str:
    """Convert an amount from one currency to another.

    Uses ECB daily reference rates via the Frankfurter API.

    Args:
        amount: The amount to convert, e.g. ``250``.
        base: Currency the amount is in, e.g. ``USD``.
        target: Currency to convert to, e.g. ``CNY``.

    Returns:
        The converted amount and the rate used — or an error message.
    """
    base, target = base.strip().upper(), target.strip().upper()
    if len(base) != 3 or len(target) != 3:
        return "Error: currency codes must be 3 letters, e.g. USD, EUR, CNY."
    try:
        data = _fetch_fx(amount, base, target)
        converted = data["rates"][target]
    except httpx.HTTPStatusError as exc:
        return (
            f"Error: Frankfurter API returned HTTP {exc.response.status_code}. "
            f"'{base}' or '{target}' may not be a supported currency code."
        )
    except (httpx.HTTPError, httpx.InvalidURL, KeyError, TypeError, ValueError) as exc:
        return f"Error: failed to convert {base}->{target}: {exc}"
    rate = converted / amount if amount else 0.0
    return (
        f"{amount:,.2f} {base} = {converted:,.2f} {target}\n"
        f"Rate: 1 {base} = {rate:.4f} {target} "
        f"(reference date {data.get('date', 'n/a')}, ECB via Frankfurter)"
    )


def main() -> None:
    """Entry point: run the MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
