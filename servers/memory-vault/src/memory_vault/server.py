"""memory-vault MCP server.

A persistent notebook for agents: save notes, then find them again later with
SQLite FTS5 full-text search — across sessions, across days. Uses only the
Python standard library (``sqlite3``); your data never leaves the machine.

The database lives at ``$MEMORY_VAULT_DB`` or, by default, ``~/.memory-vault.db``.

Run with: ``memory-vault`` (stdio transport).
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("memory-vault")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
    title, content, tags, content='notes', content_rowid='id'
);
CREATE TRIGGER IF NOT EXISTS notes_ai AFTER INSERT ON notes BEGIN
    INSERT INTO notes_fts(rowid, title, content, tags)
    VALUES (new.id, new.title, new.content, new.tags);
END;
CREATE TRIGGER IF NOT EXISTS notes_ad AFTER DELETE ON notes BEGIN
    INSERT INTO notes_fts(notes_fts, rowid, title, content, tags)
    VALUES ('delete', old.id, old.title, old.content, old.tags);
END;
CREATE TRIGGER IF NOT EXISTS notes_au AFTER UPDATE ON notes BEGIN
    INSERT INTO notes_fts(notes_fts, rowid, title, content, tags)
    VALUES ('delete', old.id, old.title, old.content, old.tags);
    INSERT INTO notes_fts(rowid, title, content, tags)
    VALUES (new.id, new.title, new.content, new.tags);
END;
"""


def db_path() -> Path:
    """Resolve the database path from ``MEMORY_VAULT_DB`` or the default."""
    raw = os.environ.get("MEMORY_VAULT_DB")
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".memory-vault.db"


def _connect() -> sqlite3.Connection:
    """Open a connection to the vault, creating the schema on first use."""
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def _now() -> str:
    """Current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _format_note(row: sqlite3.Row, *, full: bool = False) -> str:
    """Render one note row; truncated preview unless ``full`` is set."""
    content = row["content"]
    if not full and len(content) > 200:
        content = content[:200].rstrip() + "…"
    tags = row["tags"] or "(none)"
    return (
        f"#{row['id']} {row['title']}\n"
        f"Tags: {tags} | Created: {row['created_at']} | Updated: {row['updated_at']}\n"
        f"{content}"
    )


def _fts_query(raw: str) -> str:
    """Turn free text into a safe FTS5 query (quoted terms, implicit AND)."""
    terms = [term.replace('"', '""') for term in raw.split() if term.strip()]
    return " ".join(f'"{term}"' for term in terms)


@mcp.tool()
def save_note(title: str, content: str, tags: str = "") -> str:
    """Save a note to the vault so it can be found in future sessions.

    Args:
        title: A short, descriptive title for the note.
        content: The note body. Markdown is fine.
        tags: Optional comma-separated tags, e.g. ``"travel, japan, ideas"``.

    Returns:
        A confirmation including the new note's ID, or an error message.
    """
    if not title.strip():
        return "Error: title must not be empty."
    if not content.strip():
        return "Error: content must not be empty."
    normalized_tags = ", ".join(t.strip() for t in tags.split(",") if t.strip())
    try:
        with _connect() as conn:
            cursor = conn.execute(
                "INSERT INTO notes (title, content, tags, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (title.strip(), content, normalized_tags, _now(), _now()),
            )
            note_id = cursor.lastrowid
    except sqlite3.Error as exc:
        return f"Error: failed to save note: {exc}"
    return f"Saved note #{note_id}: {title.strip()}"


@mcp.tool()
def update_note(
    note_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    tags: Optional[str] = None,
) -> str:
    """Update an existing note in the vault.

    Only the fields you pass are changed; omit a field (or pass ``None``)
    to keep its current value. Passing a field replaces it wholesale:
    ``content=""`` empties the note's body and ``tags=""`` clears all its
    tags. A title cannot be cleared — a passed title must be non-empty
    (the same rule ``save_note`` applies).

    Args:
        note_id: The numeric ID of the note to update.
        title: New title, or omit to keep the current one.
        content: New body text, or omit to keep the current one;
            ``""`` clears the body.
        tags: New comma-separated tag list replacing the whole list, or
            omit to keep current tags; ``""`` clears all tags.

    Returns:
        A confirmation, or an error message if the note does not exist or
        nothing was provided to change.
    """
    if title is None and content is None and tags is None:
        return "Error: provide at least one of title, content, or tags to update."
    if title is not None and not title.strip():
        return "Error: title must not be empty."
    new_tags = None
    if tags is not None:
        new_tags = ", ".join(t.strip() for t in tags.split(",") if t.strip())
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT * FROM notes WHERE id = ?", (note_id,)
            ).fetchone()
            if row is None:
                return f"Error: no note with ID {note_id}."
            conn.execute(
                "UPDATE notes SET title = ?, content = ?, tags = ?, updated_at = ? "
                "WHERE id = ?",
                (
                    title.strip() if title is not None else row["title"],
                    content if content is not None else row["content"],
                    new_tags if new_tags is not None else row["tags"],
                    _now(),
                    note_id,
                ),
            )
    except sqlite3.Error as exc:
        return f"Error: failed to update note: {exc}"
    return f"Updated note #{note_id}."


@mcp.tool()
def search_notes(query: str, limit: int = 20) -> str:
    """Full-text search the vault (title, content, and tags).

    Args:
        query: Words to search for. Notes containing all words rank first
            (FTS5 relevance order).
        limit: Maximum number of notes to return (1-100, default 20).
            The result always reports the total number of matches, so a
            truncated list is never mistaken for the whole vault.

    Returns:
        Matching notes with previews, best matches first — or a message
        saying nothing matched.
    """
    if not query.strip():
        return "Error: query must not be empty."
    limit = max(1, min(limit, 100))
    fts = _fts_query(query)
    try:
        with _connect() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM notes_fts WHERE notes_fts MATCH ?",
                (fts,),
            ).fetchone()[0]
            rows = conn.execute(
                "SELECT n.* FROM notes n "
                "JOIN notes_fts f ON f.rowid = n.id "
                "WHERE notes_fts MATCH ? ORDER BY rank LIMIT ?",
                (fts, limit),
            ).fetchall()
    except sqlite3.Error as exc:
        return f"Error: search failed: {exc}"
    if not rows:
        return f"No notes match '{query}'."
    header = f"Found {total} note(s) matching '{query}'"
    if total > len(rows):
        header += f" (showing first {len(rows)})"
    header += ":\n"
    result = header + "\n\n".join(_format_note(r) for r in rows)
    if total > len(rows):
        result += "\n\nMore matches exist — narrow the query or raise limit (max 100)."
    return result


@mcp.tool()
def list_notes(tag: str = "", limit: int = 20) -> str:
    """List notes in the vault, most recently updated first.

    Args:
        tag: Optional — only list notes carrying this tag.
        limit: Maximum number of notes to return (1-100, default 20).
            The result always reports the total number of matching notes,
            so a truncated list is never mistaken for the whole vault.

    Returns:
        A list of notes with previews, or a message if the vault is empty.
    """
    limit = max(1, min(limit, 100))
    try:
        with _connect() as conn:
            if tag.strip():
                total = conn.execute(
                    "SELECT COUNT(*) FROM notes WHERE ',' || REPLACE(tags, ', ', ',') "
                    "|| ',' LIKE '%,' || ? || ',%'",
                    (tag.strip(),),
                ).fetchone()[0]
                rows = conn.execute(
                    "SELECT * FROM notes WHERE ',' || REPLACE(tags, ', ', ',') || ',' "
                    "LIKE '%,' || ? || ',%' ORDER BY updated_at DESC LIMIT ?",
                    (tag.strip(), limit),
                ).fetchall()
            else:
                total = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
                rows = conn.execute(
                    "SELECT * FROM notes ORDER BY updated_at DESC LIMIT ?", (limit,)
                ).fetchall()
    except sqlite3.Error as exc:
        return f"Error: failed to list notes: {exc}"
    if not rows:
        suffix = f" with tag '{tag.strip()}'" if tag.strip() else ""
        return f"No notes in the vault{suffix}."
    header = f"{total} note(s) in the vault"
    if total > len(rows):
        header += f" (showing first {len(rows)})"
    header += ":\n"
    result = header + "\n\n".join(_format_note(r) for r in rows)
    if total > len(rows):
        result += "\n\nMore notes exist — filter by tag or raise limit (max 100)."
    return result


@mcp.tool()
def get_note(note_id: int) -> str:
    """Get one note by its ID, with its full content.

    Args:
        note_id: The numeric ID returned by ``save_note`` (shown as ``#id``
            in search/list results).

    Returns:
        The full note, or an error message if no such note exists.
    """
    try:
        with _connect() as conn:
            row = conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    except sqlite3.Error as exc:
        return f"Error: failed to read note: {exc}"
    if row is None:
        return f"Error: no note with ID {note_id}."
    return _format_note(row, full=True)


@mcp.tool()
def delete_note(note_id: int) -> str:
    """Permanently delete a note from the vault.

    Args:
        note_id: The numeric ID of the note to delete.

    Returns:
        A confirmation, or an error message if no such note exists.
    """
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT title FROM notes WHERE id = ?", (note_id,)
            ).fetchone()
            if row is None:
                return f"Error: no note with ID {note_id}."
            conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    except sqlite3.Error as exc:
        return f"Error: failed to delete note: {exc}"
    return f"Deleted note #{note_id}: {row['title']}"


def main() -> None:
    """Entry point: run the MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
