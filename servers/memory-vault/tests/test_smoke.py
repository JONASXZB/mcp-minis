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
