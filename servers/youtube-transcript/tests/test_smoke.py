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
