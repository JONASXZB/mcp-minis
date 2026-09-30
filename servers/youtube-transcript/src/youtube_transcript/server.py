"""youtube-transcript MCP server.

Fetch YouTube captions as timestamped text so an agent can read, summarize,
or quote a video without watching it. No API key required — uses the
``youtube-transcript-api`` package.

Run with: ``youtube-transcript`` (stdio transport).
"""

from __future__ import annotations

import re

from mcp.server.fastmcp import FastMCP
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
)

mcp = FastMCP("youtube-transcript")

_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_URL_ID_RES = [
    re.compile(r"[?&]v=([A-Za-z0-9_-]{11})"),  # watch?v=...
    re.compile(r"youtu\.be/([A-Za-z0-9_-]{11})"),  # short links
    re.compile(r"/(?:shorts|embed|live|v)/([A-Za-z0-9_-]{11})"),  # shorts/embed/live
]


def extract_video_id(video: str) -> str | None:
    """Extract an 11-character YouTube video ID from a URL or bare ID.

    Args:
        video: A YouTube URL (watch, youtu.be, shorts, embed, live) or a
            bare video ID.

    Returns:
        The video ID, or ``None`` if no ID could be found.
    """
    candidate = video.strip()
    if _VIDEO_ID_RE.match(candidate):
        return candidate
    for pattern in _URL_ID_RES:
        match = pattern.search(candidate)
        if match:
            return match.group(1)
    return None


def _format_timestamp(seconds: float) -> str:
    """Format seconds as ``HH:MM:SS``."""
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _friendly_error(exc: Exception, video_id: str) -> str:
    """Translate youtube-transcript-api exceptions into readable messages."""
    if isinstance(exc, TranscriptsDisabled):
        return f"Error: transcripts are disabled for video '{video_id}'."
    if isinstance(exc, NoTranscriptFound):
        return f"Error: no transcript found for video '{video_id}' in the requested languages."
    if isinstance(exc, VideoUnavailable):
        return f"Error: video '{video_id}' is unavailable (private, deleted, or region-locked)."
    return f"Error: failed to fetch transcript for '{video_id}': {exc}"


@mcp.tool()
def get_transcript(video: str, languages: str = "en") -> str:
    """Get the transcript of a YouTube video as timestamped text.

    Args:
        video: A YouTube URL (any common form) or a bare 11-character video ID.
        languages: Comma-separated language codes in order of preference,
            e.g. ``"en"`` or ``"de,en"``. The first available one is used.

    Returns:
        The transcript with ``[HH:MM:SS]`` timestamps, one caption line per
        line of text — or an error message if no transcript is available.
    """
    video_id = extract_video_id(video)
    if video_id is None:
        return f"Error: could not extract a video ID from '{video}'."
    lang_list = [lang.strip() for lang in languages.split(",") if lang.strip()] or ["en"]
    api = YouTubeTranscriptApi()
    try:
        fetched = api.fetch(video_id, languages=lang_list)
    except Exception as exc:  # noqa: BLE001 - report, don't crash
        return _friendly_error(exc, video_id)
    lines = [
        f"[{_format_timestamp(snippet.start)}] {snippet.text.strip()}"
        for snippet in fetched.snippets
        if snippet.text.strip()
    ]
    if not lines:
        return f"Error: transcript for '{video_id}' was empty."
    header = f"Transcript of {video_id} ({fetched.language}, {len(lines)} lines):\n"
    return header + "\n".join(lines)


@mcp.tool()
def list_transcripts(video: str) -> str:
    """List the transcripts (caption tracks) available for a YouTube video.

    Args:
        video: A YouTube URL (any common form) or a bare 11-character video ID.

    Returns:
        One line per available transcript with its language, whether it was
        auto-generated, and whether it can be translated — or an error message.
    """
    video_id = extract_video_id(video)
    if video_id is None:
        return f"Error: could not extract a video ID from '{video}'."
    api = YouTubeTranscriptApi()
    try:
        transcript_list = api.list(video_id)
        transcripts = list(transcript_list)
    except Exception as exc:  # noqa: BLE001
        return _friendly_error(exc, video_id)
    if not transcripts:
        return f"No transcripts available for video '{video_id}'."
    lines = [f"Available transcripts for {video_id}:"]
    for transcript in transcripts:
        kind = "auto-generated" if transcript.is_generated else "manual"
        translatable = "translatable" if transcript.is_translatable else "not translatable"
        lines.append(
            f"- {transcript.language} ({transcript.language_code}) — {kind}, {translatable}"
        )
    return "\n".join(lines)


def main() -> None:
    """Entry point: run the MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
