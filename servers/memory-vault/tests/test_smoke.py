"""Smoke tests for memory-vault (stdlib only, uses a temp database)."""

import re

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
    assert names == {"save_note", "search_notes", "list_notes", "get_note", "delete_note"}


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


def test_search_is_safe_against_fts_syntax():
    server.save_note("Symbols", "Notes about *stars* and (parens).")
    # Raw FTS operators in the query must not crash the search.
    result = server.search_notes('* OR "unbalanced')
    assert isinstance(result, str)
