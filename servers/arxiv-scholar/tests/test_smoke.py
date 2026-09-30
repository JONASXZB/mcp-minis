"""Smoke tests for arxiv-scholar (no network access required)."""

from arxiv_scholar import server


def test_tools_are_registered():
    tools = server.mcp._tool_manager.list_tools()
    names = {tool.name for tool in tools}
    assert names == {"search_papers", "get_paper", "export_bibtex"}


def test_search_rejects_empty_query():
    assert "Error" in server.search_papers("")


def test_search_rejects_bad_sort():
    assert "Error" in server.search_papers("attention", sort_by="bogus")


def test_export_bibtex_rejects_empty_list():
    assert "Error" in server.export_bibtex([])


def test_get_paper_rejects_empty_id():
    assert "Error" in server.get_paper("   ")
