"""web-to-markdown MCP server.

Fetch a web page, strip the navigation/ads/boilerplate with trafilatura, and
return the main content as clean Markdown that an agent can actually read.
No API key required.

Run with: ``web-to-markdown`` (stdio transport).
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

import httpx
import trafilatura
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("web-to-markdown")

_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
_TIMEOUT_SECONDS = 30.0


def _validate_url(url: str) -> str | None:
    """Return an error message if the URL is not a plausible http(s) URL."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in {"http", "https"}:
        return f"Error: URL must start with http:// or https://, got '{url}'."
    if not parsed.netloc:
        return f"Error: URL has no host: '{url}'."
    return None


def _fetch_html(url: str) -> str:
    """Download a page's HTML with a browser-like User-Agent.

    Raises:
        httpx.HTTPError: On network errors or non-2xx responses.
    """
    headers = {"User-Agent": _USER_AGENT, "Accept": "text/html,application/xhtml+xml"}
    with httpx.Client(follow_redirects=True, timeout=_TIMEOUT_SECONDS) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.text


@mcp.tool()
def fetch_markdown(url: str, max_chars: int = 20000) -> str:
    """Fetch a web page and return its main content as Markdown.

    Navigation, ads, and other boilerplate are removed automatically.

    Args:
        url: The http(s) URL of the page to read.
        max_chars: Maximum number of characters to return (default 20000).
            Longer pages are truncated with a note.

    Returns:
        The page content as Markdown, prefixed with the page title — or an
        error message if the page cannot be fetched or no content extracted.
    """
    error = _validate_url(url)
    if error:
        return error
    if max_chars < 1:
        return "Error: max_chars must be at least 1."
    try:
        html = _fetch_html(url)
    except httpx.HTTPStatusError as exc:
        return f"Error: fetching '{url}' returned HTTP {exc.response.status_code}."
    except (httpx.HTTPError, httpx.InvalidURL) as exc:
        return f"Error: failed to fetch '{url}': {exc}"
    markdown = trafilatura.extract(
        html,
        output_format="markdown",
        include_links=True,
        include_images=False,
        include_tables=True,
    )
    if not markdown:
        return (
            f"Error: no readable content could be extracted from '{url}'. "
            "The page may be JavaScript-only, paywalled, or empty."
        )
    metadata = trafilatura.extract_metadata(html)
    title = metadata.title if metadata and metadata.title else None
    body = markdown.strip()
    if len(body) > max_chars:
        body = body[:max_chars].rstrip() + f"\n\n[Truncated at {max_chars} characters]"
    if title:
        return f"# {title}\n\nSource: {url}\n\n{body}"
    return f"Source: {url}\n\n{body}"


@mcp.tool()
def fetch_title_and_summary(url: str) -> str:
    """Fetch a page's title and a short summary without the full text.

    Useful for triaging links before deciding which ones to read in full.

    Args:
        url: The http(s) URL of the page.

    Returns:
        Title, source URL, author/date when available, and a summary built
        from the page's meta description or the opening of its main text —
        or an error message.
    """
    error = _validate_url(url)
    if error:
        return error
    try:
        html = _fetch_html(url)
    except httpx.HTTPStatusError as exc:
        return f"Error: fetching '{url}' returned HTTP {exc.response.status_code}."
    except (httpx.HTTPError, httpx.InvalidURL) as exc:
        return f"Error: failed to fetch '{url}': {exc}"
    metadata = trafilatura.extract_metadata(html)
    title = metadata.title if metadata and metadata.title else "(no title found)"
    lines = [f"Title: {title}", f"URL: {url}"]
    if metadata:
        if metadata.author:
            lines.append(f"Author: {metadata.author}")
        if metadata.date:
            lines.append(f"Date: {metadata.date}")
    summary = metadata.description if metadata and metadata.description else None
    if not summary:
        text = trafilatura.extract(html, output_format="txt")
        if text:
            flat = re.sub(r"\s+", " ", text).strip()
            summary = flat[:400] + ("…" if len(flat) > 400 else "")
    lines.append(f"Summary: {summary or '(no summary available)'}")
    return "\n".join(lines)


def main() -> None:
    """Entry point: run the MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
