"""Smoke tests for web-to-markdown (no network access required)."""

import httpx
import pytest

from web_to_markdown import server

SAMPLE_HTML = """
<html>
  <head><title>Test Page</title></head>
  <body>
    <nav>Home | About | Contact</nav>
    <article>
      <h1>Hello Reader</h1>
      <p>This is the main content of the test page. It has enough text for the
      extractor to recognize it as the primary article body of the document.</p>
      <p>A second paragraph with more substance, so extraction heuristics are
      satisfied and boilerplate such as the navigation is left behind.</p>
    </article>
    <footer>Copyright nobody.</footer>
  </body>
</html>
"""


def test_tools_are_registered():
    tools = server.mcp._tool_manager.list_tools()
    names = {tool.name for tool in tools}
    assert names == {"fetch_markdown", "fetch_title_and_summary"}


def test_validate_url_rejects_bad_input():
    assert server._validate_url("ftp://example.com/x") is not None
    assert server._validate_url("not a url") is not None
    assert server._validate_url("https://example.com/page") is None


def test_fetch_markdown_extracts_content(monkeypatch):
    monkeypatch.setattr(server, "_fetch_html", lambda url: SAMPLE_HTML)
    out = server.fetch_markdown("https://example.com/page")
    assert "Hello Reader" in out
    assert "main content of the test page" in out


def test_fetch_markdown_http_error(monkeypatch):
    def boom(url):
        request = httpx.Request("GET", url)
        response = httpx.Response(404, request=request)
        raise httpx.HTTPStatusError("not found", request=request, response=response)

    monkeypatch.setattr(server, "_fetch_html", boom)
    assert "HTTP 404" in server.fetch_markdown("https://example.com/missing")


def _client_factory(transport):
    real_client = httpx.Client

    def factory(**kwargs):
        return real_client(transport=transport, **kwargs)

    return factory


def test_fetch_html_streams_normal_page(monkeypatch):
    def handler(request):
        return httpx.Response(
            200,
            content=SAMPLE_HTML.encode(),
            headers={"Content-Type": "text/html; charset=utf-8"},
        )

    monkeypatch.setattr(
        server.httpx, "Client", _client_factory(httpx.MockTransport(handler))
    )
    html = server._fetch_html("https://example.com/page")
    assert "Hello Reader" in html


def test_fetch_html_rejects_oversized_page(monkeypatch):
    monkeypatch.setattr(server, "_MAX_RESPONSE_BYTES", 1024)

    def handler(request):
        return httpx.Response(200, content=b"x" * 5000)

    monkeypatch.setattr(
        server.httpx, "Client", _client_factory(httpx.MockTransport(handler))
    )
    with pytest.raises(server._PageTooLarge):
        server._fetch_html("https://example.com/big")


def test_tools_report_oversized_page(monkeypatch):
    def too_big(url):
        raise server._PageTooLarge(url)

    monkeypatch.setattr(server, "_fetch_html", too_big)
    assert "download limit" in server.fetch_markdown("https://example.com/big")
    assert "download limit" in server.fetch_title_and_summary("https://example.com/big")
