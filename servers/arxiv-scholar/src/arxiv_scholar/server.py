"""arxiv-scholar MCP server.

Search arXiv, fetch paper metadata, and export BibTeX citations — no API key
required. Uses the official arXiv API via the ``arxiv`` Python package.

Run with: ``arxiv-scholar`` (stdio transport).
"""

from __future__ import annotations

import re

import arxiv
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("arxiv-scholar")

_SORT_ORDERS = {
    "relevance": arxiv.SortCriterion.Relevance,
    "submitted_date": arxiv.SortCriterion.SubmittedDate,
    "last_updated": arxiv.SortCriterion.LastUpdatedDate,
}

_client = arxiv.Client(page_size=25, delay_seconds=3.0, num_retries=3)


def _normalize_arxiv_id(raw: str) -> str:
    """Reduce the ways a caller can write an arXiv ID to the bare ID.

    Accepts a bare new-style ID (``1706.03762``), a bare old-style ID
    (``hep-th/9901001``, the pre-2007 format that keeps its archive name),
    either with an ``arxiv:`` prefix, and abs/pdf URLs. Returns ``""``
    when nothing ID-like remains.
    """
    text = raw.strip().removeprefix("arxiv:")
    for marker in ("/abs/", "/pdf/"):
        if marker in text:
            text = text.split(marker, 1)[1]
            break
    else:
        if "://" in text:
            # Some other URL shape: fall back to the last path segment.
            text = text.rstrip("/").split("/")[-1]
    text = text.strip().rstrip("/")
    if text.endswith(".pdf"):
        text = text[: -len(".pdf")]
    return text


def _strip_version(arxiv_id: str) -> str:
    """Drop a trailing version suffix (``v2``) from an arXiv ID."""
    return re.sub(r"v\d+$", "", arxiv_id)


def _format_paper(result: arxiv.Result) -> str:
    """Render one arXiv result as a compact, human-readable block."""
    authors = ", ".join(author.name for author in result.authors)
    categories = ", ".join(result.categories)
    published = result.published.strftime("%Y-%m-%d") if result.published else "n/a"
    lines = [
        f"Title: {result.title}",
        f"arXiv ID: {result.get_short_id()}",
        f"Authors: {authors}",
        f"Published: {published}",
        f"Categories: {categories}",
        f"Abstract URL: {result.entry_id}",
        f"PDF URL: {result.pdf_url}",
        "",
        "Abstract:",
        " ".join(result.summary.split()),
    ]
    return "\n".join(lines)


def _bibtex_key(result: arxiv.Result) -> str:
    """Build a BibTeX citation key like ``vaswani2017attention``."""
    first_author = result.authors[0].name.split()[-1] if result.authors else "unknown"
    year = result.published.year if result.published else 0
    title_words = re.findall(r"[a-z0-9]+", result.title.lower())
    first_word = title_words[0] if title_words else "paper"
    return f"{first_author.lower()}{year}{first_word}"


_LATEX_SPECIALS = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def _latex_escape(text: str) -> str:
    """Escape LaTeX special characters so a BibTeX field stays valid.

    Applied to free-text fields (title, authors) only — URLs and arXiv IDs
    must pass through untouched, since escaping their ``_``/``~`` would
    break them.
    """
    return "".join(_LATEX_SPECIALS.get(char, char) for char in text)


def _to_bibtex(result: arxiv.Result) -> str:
    """Convert one arXiv result to a BibTeX ``@misc`` entry."""
    authors = " and ".join(_latex_escape(author.name) for author in result.authors)
    year = result.published.year if result.published else ""
    eprint = re.sub(r"v\d+$", "", result.get_short_id())
    return (
        f"@misc{{{_bibtex_key(result)},\n"
        f"  title = {{{_latex_escape(result.title)}}},\n"
        f"  author = {{{authors}}},\n"
        f"  year = {{{year}}},\n"
        f"  eprint = {{{eprint}}},\n"
        f"  archivePrefix = {{arXiv}},\n"
        f"  primaryClass = {{{result.primary_category}}},\n"
        f"  url = {{{result.entry_id}}}\n"
        f"}}"
    )


@mcp.tool()
def search_papers(query: str, max_results: int = 5, sort_by: str = "relevance") -> str:
    """Search arXiv for papers matching a query.

    Args:
        query: Free-text search query. Supports arXiv field prefixes such as
            ``ti:`` (title), ``au:`` (author), and ``abs:`` (abstract), plus
            boolean operators, e.g. ``au:vaswani AND ti:attention``.
        max_results: Maximum number of papers to return (1-25).
        sort_by: One of ``relevance``, ``submitted_date``, or ``last_updated``.

    Returns:
        A formatted list of papers with title, arXiv ID, authors, date,
        categories, links, and abstract — or an error message.
    """
    if not query.strip():
        return "Error: query must not be empty."
    if sort_by not in _SORT_ORDERS:
        return (
            f"Error: sort_by must be one of {sorted(_SORT_ORDERS)}, got '{sort_by}'."
        )
    max_results = max(1, min(max_results, 25))
    try:
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=_SORT_ORDERS[sort_by],
        )
        results = list(_client.results(search))
    except Exception as exc:  # noqa: BLE001 - surface API errors to the caller
        return f"Error: arXiv search failed: {exc}"
    if not results:
        return f"No papers found for query: {query}"
    header = f"Found {len(results)} paper(s) for '{query}':\n"
    return header + "\n\n---\n\n".join(_format_paper(r) for r in results)


@mcp.tool()
def get_paper(arxiv_id: str) -> str:
    """Fetch full metadata for a single arXiv paper by its ID.

    Args:
        arxiv_id: The arXiv identifier, new-style (``1706.03762``) or
            old-style (``hep-th/9901001``), with or without version suffix.
            A full arXiv abs/pdf URL also works.

    Returns:
        The paper's metadata and abstract, or an error message.
    """
    paper_id = _normalize_arxiv_id(arxiv_id)
    if not paper_id:
        return "Error: arxiv_id must not be empty."
    try:
        search = arxiv.Search(id_list=[paper_id])
        result = next(_client.results(search), None)
    except Exception as exc:  # noqa: BLE001
        return f"Error: failed to fetch paper '{paper_id}': {exc}"
    if result is None:
        return f"Error: no paper found with arXiv ID '{paper_id}'."
    return _format_paper(result)


@mcp.tool()
def export_bibtex(arxiv_ids: list[str]) -> str:
    """Export BibTeX entries for one or more arXiv papers.

    Args:
        arxiv_ids: List of arXiv identifiers, e.g. ``["1706.03762", "2005.11401"]``.
            Old-style IDs and arXiv URLs are accepted too.

    Returns:
        BibTeX entries ready to paste into a ``.bib`` file, or an error message.
    """
    if not arxiv_ids:
        return "Error: provide at least one arXiv ID."
    cleaned = [aid for aid in map(_normalize_arxiv_id, arxiv_ids) if aid]
    if not cleaned:
        return f"Error: none of the provided IDs resolved to a paper: {arxiv_ids}"
    try:
        search = arxiv.Search(id_list=cleaned)
        results = list(_client.results(search))
    except Exception as exc:  # noqa: BLE001
        return f"Error: failed to fetch papers: {exc}"
    if not results:
        return f"Error: none of the provided IDs resolved to a paper: {arxiv_ids}"
    found_ids = {_strip_version(r.get_short_id()) for r in results}
    entries = "\n\n".join(_to_bibtex(r) for r in results)
    missing = [aid for aid in cleaned if _strip_version(aid) not in found_ids]
    if missing:
        entries += f"\n\n% Warning: no paper found for: {', '.join(missing)}"
    return entries


def main() -> None:
    """Entry point: run the MCP server over stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
