"""Smoke tests for arxiv-scholar (no network access required)."""

from datetime import datetime

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


class _StubAuthor:
    def __init__(self, name):
        self.name = name


class _StubResult:
    """Minimal stand-in for arxiv.Result, covering what the formatters use."""

    def __init__(self, title, authors, entry_id="https://arxiv.org/abs/2401.00001"):
        self.title = title
        self.authors = [_StubAuthor(name) for name in authors]
        self.published = datetime(2024, 1, 15)
        self.primary_category = "cs.LG"
        self.entry_id = entry_id

    def get_short_id(self):
        return "2401.00001v2"


def test_bibtex_escapes_latex_specials():
    result = _StubResult(
        r"Deep Learning & AI: 100% Faster_Training #1 $5 {Draft} ~v2 ^2 \path",
        ["Jane Doe", "John Smith"],
    )
    out = server._to_bibtex(result)
    assert r"\&" in out
    assert r"100\%" in out
    assert r"Faster\_Training" in out
    assert r"\#1" in out
    assert r"\$5" in out
    assert r"\{Draft\}" in out
    assert r"\textasciitilde{}" in out
    assert r"\textasciicircum{}" in out
    assert r"\textbackslash{}" in out


def test_bibtex_leaves_url_and_plain_text_untouched():
    result = _StubResult(
        "Attention Is All You Need",
        ["Ashish Vaswani"],
        entry_id="https://example.org/paper_v2~final",
    )
    out = server._to_bibtex(result)
    assert "title = {Attention Is All You Need}" in out
    assert "author = {Ashish Vaswani}" in out
    assert "url = {https://example.org/paper_v2~final}" in out
    assert "eprint = {2401.00001}" in out
