"""Smoke tests for youtube-transcript (no network access required)."""

from youtube_transcript import server


def test_tools_are_registered():
    tools = server.mcp._tool_manager.list_tools()
    names = {tool.name for tool in tools}
    assert names == {"get_transcript", "list_transcripts"}


def test_extract_bare_id():
    assert server.extract_video_id("dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_watch_url():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s"
    assert server.extract_video_id(url) == "dQw4w9WgXcQ"


def test_extract_short_link_and_shorts():
    assert server.extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert server.extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_extract_garbage_returns_none():
    assert server.extract_video_id("not a video") is None
    assert server.get_transcript("not a video").startswith("Error")


def test_timestamp_format():
    assert server._format_timestamp(3661.7) == "01:01:01"
    assert server._format_timestamp(5) == "00:00:05"


def test_proxy_env_is_honored(monkeypatch):
    monkeypatch.delenv("HTTPS_PROXY", raising=False)
    monkeypatch.delenv("https_proxy", raising=False)
    monkeypatch.setenv("YOUTUBE_TRANSCRIPT_PROXY", "http://127.0.0.1:8080")
    api = server._build_api()
    assert api._fetcher._proxy_config is not None


def test_no_proxy_by_default(monkeypatch):
    for var in ("YOUTUBE_TRANSCRIPT_PROXY", "HTTPS_PROXY", "https_proxy"):
        monkeypatch.delenv(var, raising=False)
    api = server._build_api()
    assert api._fetcher._proxy_config is None


class _FakeApi:
    """Stand-in for YouTubeTranscriptApi returning canned snippets."""

    def __init__(self, snippets):
        self._snippets = snippets

    def fetch(self, video_id, languages=None):
        from types import SimpleNamespace

        return SimpleNamespace(
            snippets=self._snippets, language="English", language_code="en"
        )


def _install_fake_api(monkeypatch, n=5):
    from types import SimpleNamespace

    snippets = [
        SimpleNamespace(start=float(i * 10), text=f"line {i}") for i in range(n)
    ]
    monkeypatch.setattr(server, "_build_api", lambda: _FakeApi(snippets))


def test_get_transcript_full_by_default(monkeypatch):
    _install_fake_api(monkeypatch)
    out = server.get_transcript("dQw4w9WgXcQ")
    assert "(English, 5 lines)" in out
    assert "line 0" in out and "line 4" in out


def test_get_transcript_paging(monkeypatch):
    _install_fake_api(monkeypatch)
    out = server.get_transcript("dQw4w9WgXcQ", start_line=1, max_lines=2)
    assert "lines 2-3 of 5" in out
    assert "line 1" in out and "line 2" in out
    assert "line 0" not in out and "line 3" not in out


def test_get_transcript_start_beyond_end(monkeypatch):
    _install_fake_api(monkeypatch)
    out = server.get_transcript("dQw4w9WgXcQ", start_line=99)
    assert out.startswith("Error")
    assert "5 lines" in out


def test_blocked_ip_error_mentions_proxy():
    from youtube_transcript_api._errors import IpBlocked, RequestBlocked

    for exc in (RequestBlocked("dQw4w9WgXcQ"), IpBlocked("dQw4w9WgXcQ")):
        msg = server._friendly_error(exc, "dQw4w9WgXcQ")
        assert msg.startswith("Error")
        assert "YOUTUBE_TRANSCRIPT_PROXY" in msg
