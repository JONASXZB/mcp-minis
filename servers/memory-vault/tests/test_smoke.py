"""Smoke tests for memory-vault (stdlib only, uses a temp database)."""

import re
import sqlite3

import pytest

from memory_vault import server


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("MEMORY_VAULT_DB", str(tmp_path / "test-vault.db"))


def _saved_id(result: str) -> int:
    match = re.search(r"#(\d+)", result)
    assert match, f"no note id in: {result}"
    return int(match.group(1))


def test_tools_are_registered():
    tools = server.mcp._tool_manager.list_tools()
    names = {tool.name for tool in tools}
    assert names == {
        "save_note",
        "update_note",
        "search_notes",
        "list_notes",
        "get_note",
        "delete_note",
    }


def test_save_search_get_delete_round_trip():
    note_id = _saved_id(
        server.save_note("Kyoto plan", "Visit Fushimi Inari early morning.", "travel, japan")
    )
    assert "Fushimi Inari" in server.search_notes("Fushimi")
    assert "Kyoto plan" in server.list_notes()
    assert "Kyoto plan" in server.list_notes(tag="japan")
    full = server.get_note(note_id)
    assert "Visit Fushimi Inari early morning." in full
    assert "Deleted" in server.delete_note(note_id)
    assert "No notes match" in server.search_notes("Fushimi")
    assert "Error" in server.get_note(note_id)


def test_validation_errors():
    assert "Error" in server.save_note("", "content")
    assert "Error" in server.save_note("title", "  ")
    assert "Error" in server.search_notes("")
    assert "Error" in server.get_note(999)
    assert "Error" in server.delete_note(999)


def test_update_note():
    note_id = _saved_id(server.save_note("Draft", "old body", "a"))
    assert "Updated" in server.update_note(note_id, content="new body")
    full = server.get_note(note_id)
    assert "new body" in full and "Draft" in full  # title untouched
    assert "Updated" in server.update_note(note_id, title="Final", tags="b, c")
    full = server.get_note(note_id)
    assert "Final" in full and "b, c" in full
    # The FTS index must follow updates (the notes_au trigger).
    assert "Final" in server.search_notes("body")
    assert "Error" in server.update_note(note_id)  # nothing to change
    assert "Error" in server.update_note(999, title="x")  # no such note


def test_update_note_none_keeps_and_empty_string_clears():
    note_id = _saved_id(server.save_note("Keep", "original body", "a, b"))
    # Omitting tags (None) keeps the existing tag list.
    assert "Updated" in server.update_note(note_id, content="second body")
    full = server.get_note(note_id)
    assert "a, b" in full and "second body" in full
    # Passing tags="" explicitly clears the whole tag list.
    assert "Updated" in server.update_note(note_id, tags="")
    full = server.get_note(note_id)
    assert "Tags: (none)" in full
    assert "Keep" in full and "second body" in full  # other fields untouched
    # Passing content="" explicitly empties the body.
    assert "Updated" in server.update_note(note_id, content="")
    full = server.get_note(note_id)
    assert "second body" not in full
    # Passing nothing at all (all fields None) is still an error.
    assert "Error" in server.update_note(note_id)


def test_update_note_rejects_blank_title():
    note_id = _saved_id(server.save_note("Titled", "body"))
    assert "Error" in server.update_note(note_id, title="")
    assert "Error" in server.update_note(note_id, title="   ")
    assert "Titled" in server.get_note(note_id)


def test_search_is_safe_against_fts_syntax():
    server.save_note("Symbols", "Notes about *stars* and (parens).")
    # Raw FTS operators in the query must not crash the search.
    result = server.search_notes('* OR "unbalanced')
    assert isinstance(result, str)


def test_search_and_list_respect_limit_and_report_total():
    for i in range(25):
        server.save_note(f"Alpha note {i}", "common keyword body", "bulk")
    # Default limit is 20: exactly 20 notes are shown, the total is honest.
    out = server.search_notes("keyword")
    assert out.startswith("Found 25 note(s) matching 'keyword' (showing first 20):")
    assert out.count("Alpha note") == 20
    assert "More matches exist" in out
    # An explicit limit is honored.
    out = server.search_notes("keyword", limit=5)
    assert "(showing first 5)" in out
    assert out.count("Alpha note") == 5
    # Limits above the cap clamp to 100 — here all 25 fit, so no truncation.
    out = server.search_notes("keyword", limit=500)
    assert out.startswith("Found 25 note(s) matching 'keyword':")
    assert "More matches exist" not in out
    # list_notes behaves the same, with and without a tag filter.
    out = server.list_notes()
    assert out.startswith("25 note(s) in the vault (showing first 20):")
    assert out.count("Alpha note") == 20
    out = server.list_notes(tag="bulk", limit=3)
    assert out.startswith("25 note(s) in the vault (showing first 3):")
    assert out.count("Alpha note") == 3


def test_small_vault_output_is_unchanged():
    server.save_note("Only note", "a quiet body")
    out = server.search_notes("quiet")
    assert out.startswith("Found 1 note(s) matching 'quiet':")
    out = server.list_notes()
    assert out.startswith("1 note(s) in the vault:")


@pytest.mark.parametrize("tag,other", [("%", "travel"), ("a_b", "axb"), ("a%", "abc")])
def test_tag_filter_matches_literal_tags(tag, other):
    wanted_id = _saved_id(server.save_note("Wanted", "body", f"other, {tag}"))
    server.save_note("Unrelated", "body", other)
    result = server.list_notes(tag=tag)
    assert result.startswith("1 note(s) in the vault:")
    assert f"#{wanted_id} Wanted" in result
    assert "Unrelated" not in result


def test_tag_filter_remains_case_insensitive_and_matches_whole_tags():
    server.save_note("Japan", "body", "travel, Japan")
    server.save_note("Japanese", "body", "japanese")
    result = server.list_notes(tag=" JAPAN ")
    assert result.startswith("1 note(s) in the vault:")
    assert "Japanese" not in result


def test_database_connections_close_after_each_tool(monkeypatch):
    connections = []
    real_connect = sqlite3.connect

    def tracked_connect(*args, **kwargs):
        conn = real_connect(*args, **kwargs)
        connections.append(conn)
        return conn

    monkeypatch.setattr(server.sqlite3, "connect", tracked_connect)
    note_id = _saved_id(server.save_note("Title", "body"))
    operations = [
        lambda: server.update_note(note_id, content="updated body"),
        lambda: server.search_notes("body"),
        server.list_notes,
        lambda: server.get_note(note_id),
        lambda: server.delete_note(note_id),
        lambda: server.get_note(note_id),
    ]
    for operation in operations:
        operation()
    assert len(connections) == 7
    for conn in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            conn.execute("SELECT 1")


@pytest.mark.parametrize("operation", [
    lambda: server.save_note("Title", "body"),
    lambda: server.update_note(1, title="New title"),
    lambda: server.search_notes("body"),
    server.list_notes,
    lambda: server.get_note(1),
    lambda: server.delete_note(1),
])
def test_database_directory_errors_are_reported(tmp_path, monkeypatch, operation):
    parent_file = tmp_path / "not-a-directory"
    parent_file.write_text("existing file")
    monkeypatch.setenv("MEMORY_VAULT_DB", str(parent_file / "vault.db"))
    assert operation().startswith("Error:")
    assert parent_file.read_text() == "existing file"


def test_failed_transaction_rolls_back_and_closes_connection(monkeypatch):
    real_connect = sqlite3.connect
    connections = []

    def tracked_connect(*args, **kwargs):
        conn = real_connect(*args, **kwargs)
        connections.append(conn)
        return conn

    monkeypatch.setattr(server.sqlite3, "connect", tracked_connect)
    with pytest.raises(RuntimeError, match="interrupted"):
        with server._connect() as conn:
            conn.execute(
                "INSERT INTO notes (title, content, created_at, updated_at) "
                "VALUES ('Partial', 'body', 'now', 'now')"
            )
            raise RuntimeError("interrupted")
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connections[0].execute("SELECT 1")
    assert "No notes in the vault" in server.list_notes()


def test_list_notes_breaks_timestamp_ties_by_newest_id(monkeypatch):
    monkeypatch.setattr(server, "_now", lambda: "2026-10-21T00:00:00+00:00")
    server.save_note("Earlier", "body", "same")
    server.save_note("Later", "body", "same")
    for tag in ("", "same"):
        result = server.list_notes(tag=tag, limit=1)
        assert "Later" in result and "Earlier" not in result
        assert "2 note(s) in the vault (showing first 1)" in result


def test_schema_initialization_error_closes_connection(monkeypatch):
    connections = []
    real_connect = sqlite3.connect

    class BrokenSchemaConnection(sqlite3.Connection):
        def executescript(self, sql):
            raise sqlite3.OperationalError("schema initialization failed")

    def broken_connect(*args, **kwargs):
        conn = real_connect(*args, factory=BrokenSchemaConnection, **kwargs)
        connections.append(conn)
        return conn

    monkeypatch.setattr(server.sqlite3, "connect", broken_connect)
    assert "schema initialization failed" in server.save_note("Title", "body")
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connections[0].execute("SELECT 1")
